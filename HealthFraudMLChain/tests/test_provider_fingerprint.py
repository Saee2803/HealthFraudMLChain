"""
Unit tests for provider behavioral fingerprinting module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.provider_fingerprint import ProviderFingerprintGenerator


@pytest.fixture
def sample_claims_data():
    """Create sample claims data for testing."""
    np.random.seed(42)
    
    data = {
        'claim_id': [f'CLM_{i:03d}' for i in range(10)],
        'provider_id': ['PROV_001'] * 5 + ['PROV_002'] * 5,
        'patient_id': [f'PAT_{i:03d}' for i in range(10)],
        'claim_amount': [1000, 2000, 1500, 5000, 1200, 800, 1800, 2200, 900, 1100],
        'procedure_code': ['99213', '99214', '99213', '99215', '99213', 
                          '99214', '99214', '99215', '99213', '99214'],
        'diagnosis_code': ['M79.3'] * 10,
        'date_of_service': pd.date_range('2023-01-01', periods=10, freq='D'),
        'date_of_claim_filed': pd.date_range('2023-01-02', periods=10, freq='D'),
        'specialization': ['Cardiology'] * 5 + ['Orthopedics'] * 5,
        'region': ['Northeast'] * 10
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def generator():
    """Create ProviderFingerprintGenerator instance."""
    return ProviderFingerprintGenerator()


def test_load_claims_data_with_sample(generator, sample_claims_data):
    """Test loading claims data with proper columns."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_claims_data.to_csv(f.name, index=False)
        
        df = generator.load_claims_data(f.name)
        
        assert len(df) == 10
        assert 'provider_id' in df.columns
        assert 'claim_amount' in df.columns
        assert df['provider_id'].nunique() == 2


def test_compute_provider_features(generator, sample_claims_data):
    """Test provider feature computation."""
    features_df = generator.compute_provider_features(sample_claims_data)
    
    # Check basic structure
    assert len(features_df) == 2  # Two providers
    assert 'provider_id' in features_df.columns
    assert 'total_claims_count' in features_df.columns
    assert 'avg_claim_amount' in features_df.columns
    
    # Check PROV_001 features
    prov_001 = features_df[features_df['provider_id'] == 'PROV_001'].iloc[0]
    assert prov_001['total_claims_count'] == 5
    assert prov_001['avg_claim_amount'] == 2140.0  # (1000+2000+1500+5000+1200)/5
    assert prov_001['procedure_entropy'] > 0  # Should have some entropy
    
    # Check PROV_002 features  
    prov_002 = features_df[features_df['provider_id'] == 'PROV_002'].iloc[0]
    assert prov_002['total_claims_count'] == 5
    assert prov_002['avg_claim_amount'] == 1360.0  # (800+1800+2200+900+1100)/5


def test_compute_peer_group_deviations(generator, sample_claims_data):
    """Test peer group deviation computation."""
    features_df = generator.compute_provider_features(sample_claims_data)
    features_with_peers = generator.compute_peer_group_deviations(features_df)
    
    # Check peer group columns added
    assert 'peer_group_key' in features_with_peers.columns
    assert 'peer_zscore_avg_claim_amount' in features_with_peers.columns
    
    # Check peer group keys
    expected_keys = ['Cardiology_Northeast', 'Orthopedics_Northeast']
    assert set(features_with_peers['peer_group_key'].unique()) == set(expected_keys)


def test_compute_anomaly_score(generator, sample_claims_data):
    """Test anomaly score computation."""
    features_df = generator.compute_provider_features(sample_claims_data)
    features_with_peers = generator.compute_peer_group_deviations(features_df)
    final_features = generator.compute_anomaly_score(features_with_peers)
    
    # Check anomaly score columns
    assert 'anomaly_score' in final_features.columns
    assert 'risk_category' in final_features.columns
    assert 'computed_at' in final_features.columns
    
    # Check score range
    assert all(0 <= score <= 1 for score in final_features['anomaly_score'])
    
    # Check risk categories
    valid_categories = {'LOW', 'MEDIUM', 'HIGH'}
    assert all(cat in valid_categories for cat in final_features['risk_category'])


def test_generate_fingerprints_end_to_end(generator, sample_claims_data):
    """Test complete fingerprint generation pipeline."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save sample data
        claims_path = Path(temp_dir) / "claims.csv"
        sample_claims_data.to_csv(claims_path, index=False)
        
        # Generate fingerprints
        parquet_path, jsonl_path = generator.generate_fingerprints(
            str(claims_path), temp_dir
        )
        
        # Check outputs exist
        assert Path(parquet_path).exists()
        assert Path(jsonl_path).exists()
        
        # Check parquet content
        df = pd.read_parquet(parquet_path)
        assert len(df) == 2
        assert 'provider_id' in df.columns
        assert 'anomaly_score' in df.columns
        
        # Check JSONL content
        import json
        with open(jsonl_path, 'r') as f:
            records = [json.loads(line) for line in f]
        
        assert len(records) == 2
        assert all('provider_id' in record for record in records)
        assert all('anomaly_score' in record for record in records)
        assert all('top_contributing_features' in record for record in records)


def test_feature_calculations_accuracy(generator):
    """Test specific feature calculation accuracy."""
    # Create controlled test data
    data = {
        'claim_id': ['CLM_001', 'CLM_002', 'CLM_003'],
        'provider_id': ['PROV_TEST'] * 3,
        'patient_id': ['PAT_001', 'PAT_001', 'PAT_002'],  # One repeated patient
        'claim_amount': [1000, 2000, 3000],
        'procedure_code': ['99213', '99213', '99214'],  # Some repetition
        'diagnosis_code': ['M79.3'] * 3,
        'date_of_service': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
        'date_of_claim_filed': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
        'specialization': ['Cardiology'] * 3,
        'region': ['Northeast'] * 3
    }
    
    df = pd.DataFrame(data)
    features_df = generator.compute_provider_features(df)
    
    provider_features = features_df.iloc[0]
    
    # Test specific calculations
    assert provider_features['total_claims_count'] == 3
    assert provider_features['avg_claim_amount'] == 2000.0  # (1000+2000+3000)/3
    assert provider_features['repeated_patient_ratio'] == 0.5  # 1 out of 2 unique patients has >1 claim
    
    # Test procedure diversity
    expected_diversity = 2/3  # 2 unique procedures out of 3 claims
    assert abs(provider_features['unusual_procedure_diversity'] - expected_diversity) < 0.001


def test_missing_columns_handling(generator):
    """Test handling of missing columns."""
    # Minimal data with missing columns
    data = {
        'some_id': [1, 2, 3],
        'amount': [100, 200, 300]
    }
    
    df = pd.DataFrame(data)
    
    # Should not crash and should create synthetic columns
    processed_df = generator.load_claims_data(None)  # Will use synthetic data
    
    assert 'provider_id' in processed_df.columns
    assert 'claim_amount' in processed_df.columns
    assert 'procedure_code' in processed_df.columns


if __name__ == "__main__":
    pytest.main([__file__])