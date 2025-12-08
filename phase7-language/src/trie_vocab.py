
import sys
from typing import Dict, List, Optional
import struct


import sys
import array

class TrieVocab:
    """
    Ultralight Trie using LCRS (Left-Child Right-Sibling) representation in flat arrays.
    Simulates C-level memory efficiency in Python.
    
    Nodes are indices in arrays:
    - values[i]: Character (byte)
    - child[i]: Index of first child
    - sibling[i]: Index of next sibling
    - token_id[i]: Token ID if end of word, else -1
    """
    def __init__(self):
        # Using arrays for compact storage (signed int for indices, -1 = null)
        self.char = array.array('B')       # 1 byte (unsigned)
        self.child = array.array('i')      # 4 bytes
        self.sibling = array.array('i')    # 4 bytes
        self.token_id = array.array('i')   # 4 bytes
        
        # Root node (dummy)
        self._add_node(0)
        
        self.size = 0
        
        # Reverse lookup: ID -> Word
        # Compressed string buffer
        self.word_buffer = bytearray()
        self.word_offsets = array.array('i')
        self.word_lengths = array.array('B') # Assuming max word len < 255

    def _add_node(self, char_val: int) -> int:
        idx = len(self.char)
        self.char.append(char_val)
        self.child.append(-1)
        self.sibling.append(-1)
        self.token_id.append(-1)
        return idx

    def add(self, word: str) -> int:
        if not word: return -1
        
        w_bytes = word.encode('utf-8')
        curr = 0 # Root
        
        for b in w_bytes:
            # Search children (linked list via sibling)
            found_child = -1
            child_idx = self.child[curr]
            
            prev = -1
            curr_sib = child_idx
            
            while curr_sib != -1:
                if self.char[curr_sib] == b:
                    found_child = curr_sib
                    break
                prev = curr_sib
                curr_sib = self.sibling[curr_sib]
            
            if found_child != -1:
                curr = found_child
            else:
                # Add new child
                new_node = self._add_node(b)
                if prev == -1:
                    # First child
                    self.child[curr] = new_node
                else:
                    # Append to sibling list
                    self.sibling[prev] = new_node
                curr = new_node
        
        # Mark end
        if self.token_id[curr] == -1:
            self.token_id[curr] = self.size
            self.size += 1
            
            # Store for reverse lookup
            offset = len(self.word_buffer)
            self.word_buffer.extend(w_bytes)
            self.word_offsets.append(offset)
            self.word_lengths.append(len(w_bytes))
            
        return self.token_id[curr]

    def get_id(self, word: str) -> int:
        if not word: return -1
        w_bytes = word.encode('utf-8')
        curr = 0
        
        for b in w_bytes:
            child = self.child[curr]
            while child != -1:
                if self.char[child] == b:
                    break
                child = self.sibling[child]
            
            if child == -1:
                return -1
            curr = child
            
        return self.token_id[curr]
    
    def get_word(self, idx: int) -> str:
        if idx < 0 or idx >= self.size:
            return "<UNK>"
        
        offset = self.word_offsets[idx]
        length = self.word_lengths[idx]
        return self.word_buffer[offset:offset+length].decode('utf-8')
        
    def get_memory_usage(self) -> int:
        mem = sys.getsizeof(self.char) + sys.getsizeof(self.child) + \
              sys.getsizeof(self.sibling) + sys.getsizeof(self.token_id)
        mem += sys.getsizeof(self.word_buffer) + \
               sys.getsizeof(self.word_offsets) + sys.getsizeof(self.word_lengths)
        return mem

