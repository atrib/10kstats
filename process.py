#!/usr/bin/env python3

import csv
import numpy as np
import os
import pandas as pd
import re
import matplotlib as mpl
import matplotlib.pyplot as plt

## Config vars
datadir = 'data'
gendir  = 'gen'

class Person:
  
  def __init__(self, line):
    self.id = line[0]
    self.name = line[1]
    self.yob = line[2]
    self.gender = line[3]
    self.country = line[4][0:2]
    self.city = line[5]
    self.category = line[6]
    self.block = int(line[7])
    self.start = line[8]
    
  def to_time(self, s):
    fmts = '(([12]):)?(\d{2}):(\d{2})(\.(\d))?'
    m = re.match(fmts, s)
    secs = 0
    if m is not None:
      hours = m.group(2)
      mins = int(m.group(3))
      
      secs = int(m.group(4))
      decsecs = m.group(5)
      if hours:
        secs += int(m.group(2)) * 3600
      secs += mins * 60
      
    mins = secs / 60
    
    return mins
    
  def set_result(self, line):
    id = line[0]
    assert(id == self.id)
    name = line[1]
    if name != self.name:
      print('{} {} {}'.format(self.id, name, self.name))
    # assert(name == self.name)
    yob = line[2]
    assert(yob == self.yob)
    self.result = line[3]
    self.time = self.to_time(line[4])

class Category:
  def __init__(self, name):
    self.name = name
    self.persons = []
    self.blocks = set()
    self.block_n = {}
    
  def add_person(self, person):
    self.persons.append(person)
    self.blocks.add(person.block)
    if person.block in self.block_n:
      self.block_n[person.block] += 1
    else:
      self.block_n[person.block] = 1
      
class Country:
  def __init__(self, name, ID):
    self.name = name
    self.id = id
    self.persons = []
    
  def add_person(self, person):
    self.persons.append(person)

person_by_id = {}
persons = []
categories = {}
category_names = []
blocks = []
country_ids = []
countries = {}
country_name_by_id = {}

def plot_composition():
  global persons
  global categories
  global category_names
  global blocks
  # [print(category.block_n) for cat_name, category in categories.items()]
  
  fig, ax = plt.subplots()
  bottom = [0 for block in blocks]
  idx = 0
  for category_name in category_names:
    category = categories[category_name]
    height = [category.block_n[block] if block in category.block_n else 0 for block in blocks]
    ax.bar(blocks, height, bottom = bottom, color = plt.cm.tab20(idx), label = category_name)
    
    bottom = [x + y for x, y in zip(bottom, height)]
    idx += 1
    
  ax.set_xlabel('Starting Block (proxy for indicated completion time)')
  ax.set_ylabel('People Count')
  fig.legend()
  fig.savefig(gendir + '/inscriptions_by_block.pdf', bbox_inches = 'tight')

# Assuming x is not at either extreme of x_arr
def find_height_at_x(x_arr, y_arr, x):
  prev = 0
  
  assert(len(x_arr) == len(y_arr))
  for idx in range(1, len(x_arr)):
    if x > x_arr[idx - 1] and (x < x_arr[idx]):
      return (y_arr[idx - 1] * (x_arr[idx] - x) + y_arr[idx] * (x - x_arr[idx - 1])) / (x_arr[idx] - x_arr[idx - 1])
  
    
def plot_results_by_block():
  global persons
  global blocks
  
  times_per_block = {block: [] for block in blocks}
  for person in persons:
    if hasattr(person, 'result') and person.result == 'Arrivée':
      times_per_block[person.block].append(person.time)
      
  fig, ax = plt.subplots()
  bins = list(range(30, 100, 2)) # in minutes
  bin_centers = [(x + y) / 2 for x, y in zip(bins[:-1], bins[1:])]
  idx = 0
  for block, times in times_per_block.items():
    # Plot histogram of finisher timings, but as a line plot
    n_np, _ = np.histogram(times, bins)
    ax.plot(bin_centers, n_np, color = plt.cm.tab20(idx), label = block)
    
    # Plot median, and maybe quartiles
    quartiles = np.quantile(times, [0.25, 0.5, 0.75])
    quartile_heights = [find_height_at_x(bin_centers, n_np, x) for x in quartiles]
    ax.vlines(x = quartiles[1], ymin = 0, ymax = quartile_heights[1], colors = plt.cm.tab20(idx), linestyles = 'dotted', lw = 1)
    
    idx += 1
    # break
    
  ax.set_xlabel('Finish time (finishers only) in minutes')
  ax.set_ylabel('People count')
  ax.set_xticks(range(min(bins), max(bins), 10))
  ax.set_xticks(range(min(bins), max(bins), 2), minor=True)
  ax.grid(visible = True, which = 'minor', axis = 'x', alpha = 0.2)
  ax.grid(visible = True, which = 'major', axis = 'x', alpha = 0.5)
  bottom, top = ax.get_ylim()
  ax.set_ylim(0, top)
  fig.legend()
  fig.savefig(gendir + '/results_by_block.pdf', bbox_inches = 'tight')

def plot_results_by_country():
  
  c_times = {c_id: [person.time for person in countries[c_id].persons if hasattr(person, 'result')] for c_id in country_ids}
  stats = {c_id: (len(ptimes), sum(ptimes)/len(ptimes), np.quantile(ptimes, 0.5)) for c_id, ptimes in c_times.items() if len(ptimes) > 0}
  print('{:80}\t{:10}\t{:10}\t{:10}'.format('Country name', 'Count', 'Mean', 'Median'))
  [print('{:80}\t{:10}\t{:10}\t{:10}'.format(country_name_by_id[c_id], c_stats[0], round(c_stats[1], 2), round(c_stats[2], 2))) for c_id, c_stats in sorted(stats.items(), key = lambda item: item[1][2])]

def input_data():
  global persons
  global categories
  global person_by_id
  global category_names
  global blocks
  global country_ids
  global countries
  global country_name_by_id
  
  # Input all attendees
  with open(datadir + '/inscriptions.csv') as csvfd:
    csvr = csv.reader(csvfd)
    lines = [line for line in csvr]

    # Debug check for input validity
    count = 0
    for line in lines:
      count += 1
      if(len(line) != 9):
        print('DEBUG: Error in line {}'.format(line))

    persons = [Person(line) for line in lines]
    
  # Map person by dossard
  for person in persons:
    person_by_id[person.id] = person
    
  # Input results
  with open(datadir + '/results.csv') as csvfd:
    csvr = csv.reader(csvfd)
    lines = [line for line in csvr]

    # Debug check for input validity
    for line in lines:
      if(len(line) != 5):
        print('DEBUG: Error in line {}'.format(line))
        
    for line in lines:
      id = line[0]
      try:
        person_by_id[id].set_result(line)
      except KeyError:
        print('{} missing'.format(id))
        
  
  # Group participants into categories
  category_names = list(set([person.category for person in persons]))
  category_names.sort()
  blocks = list(set([person.block for person in persons]))
  blocks.sort()

  categories = {category_name: Category(category_name) for category_name in category_names}
  [categories[person.category].add_person(person) for person in persons]
  
  # Group participants into countries
  country_ids = []
  countries_by_id = {}
  with open('countries.tsv') as csvfd:
    csvr = csv.reader(csvfd, delimiter = '\t')
    lines = [line for line in csvr]
    
    #  Debug chcek for input validity
    for line in lines:
      if(len(line) != 2):
        print('DEBUG: Error in line {}'.format(line))
    
    for line in lines:
      country_ids.append(line[1])
      countries[line[1]] = Country(line[0], line[1])
      country_name_by_id[line[1]] = line[0]
      
  [countries[person.country].add_person(person) for person in persons]
      
def main():
  input_data()
  
  if not os.path.isdir(gendir):
    os.mkdir(gendir)
  plot_composition()
  plot_results_by_block()
  plot_results_by_country()

if __name__ == '__main__':
  main()

      
  # persons = [person(line) for line in csvr]
    
  # Map each block to the persons in it
  # blocks = set()
  # for p in persons:
  #   blocks.add(p.block)
  # [print(x) for x in blocks]
  # block_person_map = {}
  # for block in blocks:
  #   block_person_map[block] = [person for person in persons if person.block == block]
  # [print(len(block_person_map[block])) for block in blocks]
  
