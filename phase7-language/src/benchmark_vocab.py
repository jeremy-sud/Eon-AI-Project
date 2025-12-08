
import sys
import random
import string
from trie_vocab import TrieVocab

def generate_vocab(n=1000, max_len=10):
    vocab = []
    chars = string.ascii_lowercase
    for _ in range(n):
        length = random.randint(3, max_len)
        word = ''.join(random.choice(chars) for _ in range(length))
        vocab.append(word)
    return vocab

def benchmark_memory():
    vocab_list = generate_vocab(5000, 12)
    
    # Standard Python Dict/List
    std_vocab_map = {w: i for i, w in enumerate(vocab_list)}
    std_vocab_list = list(vocab_list) # Reverse lookup
    
    mem_std = sys.getsizeof(std_vocab_map) + sys.getsizeof(std_vocab_list)
    # Deep size estimate
    for w in vocab_list:
        mem_std += sys.getsizeof(w) # String object overhead!
    
    # Trie Vocab
    trie = TrieVocab()
    for w in vocab_list:
        trie.add(w)
        
    mem_trie = trie.get_memory_usage()
    
    print(f"Vocab Size: {len(vocab_list)} words")
    print(f"Standard Memory: {mem_std / 1024:.2f} KB")
    print(f"Trie Memory:     {mem_trie / 1024:.2f} KB")
    print(f"Reduction:       {(1 - mem_trie/mem_std)*100:.1f}%")

if __name__ == "__main__":
    benchmark_memory()
