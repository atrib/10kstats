#!/usr/bin/env python3

import csv
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

class Person:
  
  def __init__(self, line):
    self.id = line[0]
    self.name = line[1]
    self.yob = line[2]
    self.gender = line[3]
    self.country = line[4]
    self.city = line[5]
    self.category = line[6]
    self.block = int(line[7])
    self.start = line[8]
    
  def set_result(self, line):
    id = line[0]
    assert(id == self.id)
    name = line[1]
    assert(name == self.name)
    self.result = line[2]
    self.time = line[3]

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

person_by_id = {}
persons = []
categories = {}
category_names = []
blocks = []

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
  fig.savefig('inscriptions_by_block.pdf', bbox_inches = 'tight')
  

def input_data():
  global persons
  global categories
  global person_by_id
  global category_names
  global blocks
  
  # Input all attendees
  with open('inscriptions.csv') as csvfd:
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
  with open('results.csv') as csvfd:
    csvr = csv.reader(csvfd)

    # Debug check for input validity
    for line in csvr:
      if(len(line) != 5):
        print('DEBUG: Error in line {}'.format(line))
        
    for line in csvr:
      id = line[0]
      person_by_id[id].set_result(line)
  
  # Group participants into categories
  category_names = list(set([person.category for person in persons]))
  category_names.sort()
  blocks = list(set([person.block for person in persons]))
  blocks.sort()

  categories = {category_name: Category(category_name) for category_name in category_names}
  [categories[person.category].add_person(person) for person in persons]
  
def main():
  input_data()
  plot_composition()

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
  
