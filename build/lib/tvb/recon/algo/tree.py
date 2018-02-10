# -*- coding: utf-8 -*-
"""
Created on Fri Dec 16 16:48:03 2016

@author: dionperd
"""
from anytree import Node
import numpy


def make_tree(dict_tree):
    tree = dict()
    nodes = numpy.sort(list(dict_tree.keys()))
    nodes = nodes[::-1]
    root = nodes[0]
    tree[str(root)] = Node(str(root))
    for parent in nodes[1:]:
        children = dict_tree[parent]
        for child in children:
            tree[str(child)] = Node(str(child), parent=tree[str(parent)])
    return (tree, root)


def return_tree_leafs(node):
    leafs = []
    for nod in node.descendants:
        if nod.isleaf:
            leafs.append(int(nod.name))
    return leafs

# def return_flat_clusters(root,min_area,max_area):
