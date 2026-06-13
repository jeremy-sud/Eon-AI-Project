"""
Tests for Neural Watermarking Integration in Collective Mind
============================================================
Tests that weight packets are signed, verified, and protected
against tampering using NeuralWatermark.
"""

import pytest
import numpy as np
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_phase6_dir = os.path.dirname(_current_dir)
if _phase6_dir not in sys.path:
    sys.path.insert(0, _phase6_dir)

from collective_mind import AeonNode, DataDomain, _watermark_available


def test_watermark_availability():
    """Verify if NeuralWatermark library is available for testing."""
    assert _watermark_available is True, "NeuralWatermark should be available in the environment"


class TestNeuralWatermarkIntegration:
    @pytest.fixture
    def trained_node_a(self):
        """Create a trained node representing Owner A."""
        node = AeonNode(node_id="node_alice", n_reservoir=300, genesis_domain=DataDomain.GENERIC)
        data = np.sin(np.linspace(0, 10, 500))
        node.train(data, washout=50)
        return node

    @pytest.fixture
    def trained_node_b(self):
        """Create a trained node representing Owner B."""
        node = AeonNode(node_id="node_bob", n_reservoir=300, genesis_domain=DataDomain.GENERIC)
        data = np.sin(np.linspace(0, 10, 500))
        node.train(data, washout=50)
        return node

    def test_export_1bit_contains_watermark(self, trained_node_a):
        """Test that export_weights_1bit signs weights with a watermark."""
        packet = trained_node_a.export_weights_1bit()
        
        assert "watermark" in packet
        assert packet["watermark"]["owner"] == "node_alice"
        assert "signature" in packet["watermark"]

    def test_import_valid_watermark_succeeds_1bit(self, trained_node_a, trained_node_b):
        """Test that importing weights with a valid watermark works correctly (1-bit)."""
        # Export from node_a (signed as node_alice)
        packet = trained_node_a.export_weights_1bit()
        
        # Bob knows Alice as a peer
        trained_node_b.peers.append("node_alice")
        
        # Bob imports Alice's weights (valid signature)
        success = trained_node_b.import_weights_1bit(packet, merge_ratio=0.5)
        assert success is True

    def test_import_tampered_owner_fails_1bit(self, trained_node_a, trained_node_b):
        """Test that changing the owner field on a signed 1-bit packet gets rejected."""
        # Export signed as node_alice
        packet = trained_node_a.export_weights_1bit()
        
        # Tamper the packet owner
        packet["watermark"]["owner"] = "imposter_node"
        
        # Bob imports tampered packet
        trained_node_b.peers.append("imposter_node")
        success = trained_node_b.import_weights_1bit(packet, merge_ratio=0.5)
        
        # Verification should detect mismatch (Alice's signature vs 'imposter_node')
        assert success is False

    def test_export_import_full_precision_watermark(self, trained_node_a, trained_node_b):
        """Test that full-precision weights retain and verify physical LSB watermarks."""
        # Export high-res weights (signed physically via LSB)
        weights_data = trained_node_a.export_weights()
        
        assert "watermark" in weights_data
        assert weights_data["watermark"]["owner"] == "node_alice"
        
        # Import to Node B with merge_ratio = 1.0 (direct copy)
        # to ensure the physical LSB bits are preserved exactly
        trained_node_b.peers.append("node_alice")
        success = trained_node_b.import_weights(weights_data, merge_ratio=1.0)
        assert success is True
        
        # Verify Bob's new weights are physically watermarked by Alice
        from utils.watermark import extract_owner
        owner, confidence = extract_owner(trained_node_b.esn.W_out)
        assert owner == "node_alice"

    def test_import_tampered_weights_full_precision_fails(self, trained_node_a, trained_node_b):
        """Test that modifying the signed weights of a full-precision packet gets rejected."""
        # Export high-res weights
        weights_data = trained_node_a.export_weights()
        
        # Corrupt the weights significantly to destroy physical signature bits (100 elements out of 256)
        weights_arr = np.array(weights_data["W_out"])
        W_flat = weights_arr.flatten()
        W_float64 = W_flat.astype(np.float64)
        W_uint64 = W_float64.view(np.uint64).copy()
        # Flip the LSBs of the first 100 elements
        for i in range(100):
            W_uint64[i] = W_uint64[i] ^ np.uint64(1)
        weights_data["W_out"] = W_uint64.view(np.float64).reshape(weights_arr.shape).tolist()
        
        # Bob imports corrupted weights
        trained_node_b.peers.append("node_alice")
        success = trained_node_b.import_weights(weights_data, merge_ratio=0.5)
        
        # Verification must reject tampered weights
        assert success is False
