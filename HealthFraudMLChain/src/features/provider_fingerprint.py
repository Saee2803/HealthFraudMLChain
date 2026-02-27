"""
Provider Behavioral Fingerprinting Module

Computes provider-level behavioral fingerprints from historical claims data
to detect anomalous patterns and potential fraud.
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProviderFingerprintGenerator:
    """Generates behavioral fingerprints for healthcare providers."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        
    def _default_config(self) -> Dict:
        """Default configuration for fingerprint generation."""
        return {
            'anomaly_weights': {
                'avg_claim_amount': 0.2,
                'high_cost_claim_ratio': 0.15,
                'procedure_entropy': 0.1,
                'resubmission_rate': 0.15,
                'weekend_claim_ratio': 0.1,
                'night_claim_ratio': 0.1,
                'time_to_file': 0.1,
                'repeated_patient_ratio': 0.1
            },
            'risk_thresholds': {
                'low': 0.3,
                'medium': 0.6
            },
            'lookback_months': 12
        }
    
    def _generate_synthetic_claims_data(self, num_records: int = 100) -> pd.DataFrame:
        """Generate synthetic claims data for testing or when no file is available."""
        logger.info(f"Generating {num_records} synthetic claims records")
        
        providers = [f'PROV_{i:03d}' for i in range(5)]
        patients = [f'PAT_{i:04d}' for i in range(50)]
        procedures = ['99213', '99214', '99215', '99232', '99233', '99291', '99292']
        diagnoses = ['M79.3', 'Z51.11', 'I10', 'E11.9', 'F32.9', 'J45.901', 'E27.40']
        specializations = ['Cardiology', 'Orthopedics', 'Internal Medicine', 'Surgery', 'Radiology']
        regions = ['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West']
        
        data = {
            'claim_id': [f'CLM_{i:06d}' for i in range(num_records)],
            'provider_id': [np.random.choice(providers) for _ in range(num_records)],
            'patient_id': [np.random.choice(patients) for _ in range(num_records)],
            'claim_amount': np.random.uniform(100, 50000, num_records),
            'procedure_code': [np.random.choice(procedures) for _ in range(num_records)],
            'diagnosis_code': [np.random.choice(diagnoses) for _ in range(num_records)],
            'date_of_service': pd.date_range(datetime.now() - timedelta(days=365), periods=num_records, freq='12h'),
            'date_of_claim_filed': pd.date_range(datetime.now() - timedelta(days=365), periods=num_records, freq='12h'),
        }
        
        df = pd.DataFrame(data)
        
        # Add provider-specific specialization and region
        provider_specs = {pid: np.random.choice(specializations) for pid in providers}
        provider_regions = {pid: np.random.choice(regions) for pid in providers}
        
        df['specialization'] = df['provider_id'].map(provider_specs)
        df['region'] = df['provider_id'].map(provider_regions)
        
        logger.info(f"Generated synthetic data: {len(df)} records for {df['provider_id'].nunique()} providers")
        return df
    
    def detect_claims_dataset(self, data_dir: str = "data") -> Optional[str]:
        """Auto-detect claims dataset path."""
        data_path = Path(data_dir)
        if not data_path.exists():
            return None
            
        # Look for CSV files with claim-like columns
        for csv_file in data_path.glob("*.csv"):
            try:
                df_sample = pd.read_csv(csv_file, nrows=5)
                claim_cols = {'claim_id', 'provider_id', 'claim_amount', 'procedure_code'}
                if claim_cols.issubset(set(df_sample.columns.str.lower())):
                    return str(csv_file)
            except:
                continue
        return None
    
    def load_claims_data(self, claims_path: str) -> pd.DataFrame:
        """Load and preprocess claims data. If claims_path is None, generate synthetic data."""
        # Handle None input: generate synthetic data
        if claims_path is None:
            logger.info("claims_path is None; generating synthetic data")
            return self._generate_synthetic_claims_data()
        
        logger.info(f"Loading claims data from {claims_path}")
        
        df = pd.read_csv(claims_path)
        
        # Standardize column names
        col_mapping = {
            'provider_id': 'provider_id',
            'claim_id': 'claim_id', 
            'patient_id': 'patient_id',
            'claim_amount': 'claim_amount',
            'procedure_code': 'procedure_code',
            'diagnosis_code': 'diagnosis_code',
            'date_of_service': 'date_of_service',
            'date_of_claim_filed': 'date_of_claim_filed'
        }
        
        # Handle case variations
        for old_col in df.columns:
            for std_col, new_col in col_mapping.items():
                if old_col.lower().replace('_', '').replace(' ', '') == std_col.replace('_', ''):
                    df = df.rename(columns={old_col: new_col})
                    break
        
        # Create synthetic data if columns missing
        if 'provider_id' not in df.columns:
            df['provider_id'] = 'PROV_' + (df.index % 100).astype(str).str.zfill(3)
        if 'claim_id' not in df.columns:
            df['claim_id'] = 'CLM_' + df.index.astype(str)
        if 'patient_id' not in df.columns:
            df['patient_id'] = 'PAT_' + (df.index % 500).astype(str).str.zfill(4)
        if 'claim_amount' not in df.columns:
            df['claim_amount'] = np.random.uniform(100, 50000, len(df))
        if 'procedure_code' not in df.columns:
            procedures = ['99213', '99214', '99215', '99232', '99233', '99291', '99292']
            df['procedure_code'] = np.random.choice(procedures, len(df))
        if 'diagnosis_code' not in df.columns:
            diagnoses = ['M79.3', 'Z51.11', 'I10', 'E11.9', 'F32.9']
            df['diagnosis_code'] = np.random.choice(diagnoses, len(df))
        
        # Handle dates
        if 'date_of_service' not in df.columns:
            base_date = datetime.now() - timedelta(days=365)
            df['date_of_service'] = pd.date_range(base_date, periods=len(df), freq='D')
        else:
            df['date_of_service'] = pd.to_datetime(df['date_of_service'], errors='coerce')
            
        if 'date_of_claim_filed' not in df.columns:
            df['date_of_claim_filed'] = df['date_of_service'] + pd.Timedelta(days=np.random.randint(1, 30, len(df)))
        else:
            df['date_of_claim_filed'] = pd.to_datetime(df['date_of_claim_filed'], errors='coerce')
        
        # Add synthetic provider metadata
        if 'specialization' not in df.columns:
            specializations = ['Cardiology', 'Orthopedics', 'Internal Medicine', 'Surgery', 'Radiology']
            provider_specs = {pid: np.random.choice(specializations) 
                            for pid in df['provider_id'].unique()}
            df['specialization'] = df['provider_id'].map(provider_specs)
            
        if 'region' not in df.columns:
            regions = ['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West']
            provider_regions = {pid: np.random.choice(regions) 
                              for pid in df['provider_id'].unique()}
            df['region'] = df['provider_id'].map(provider_regions)
        
        logger.info(f"Loaded {len(df)} claims for {df['provider_id'].nunique()} providers")
        return df
    
    def compute_provider_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute behavioral features for each provider. 
        
        Returns at least one row per provider_id found in df.
        Handles missing columns gracefully.
        """
        logger.info("Computing provider behavioral features")
        
        if df is None or len(df) == 0:
            logger.warning("Input dataframe is empty; returning empty features")
            return pd.DataFrame()
        
        if 'provider_id' not in df.columns:
            logger.warning("provider_id column not found; cannot compute features")
            return pd.DataFrame()
        
        # Filter to recent data if dates available (last N months from the data's max date)
        if 'date_of_service' in df.columns and not df['date_of_service'].isna().all():
            # Get the max date in the data and compute cutoff relative to that
            max_date = pd.to_datetime(df['date_of_service']).max()
            cutoff_date = max_date - timedelta(days=30 * self.config['lookback_months'])
            df = df[pd.to_datetime(df['date_of_service']) >= cutoff_date]
        
        features = []
        
        for provider_id in df['provider_id'].unique():
            provider_data = df[df['provider_id'] == provider_id].copy()
            
            if len(provider_data) == 0:
                continue
                
            feature_dict = {'provider_id': provider_id}
            
            # Basic volume metrics
            feature_dict['total_claims_count'] = len(provider_data)
            feature_dict['total_claim_amount'] = provider_data['claim_amount'].sum()
            feature_dict['avg_claim_amount'] = provider_data['claim_amount'].mean()
            feature_dict['median_claim_amount'] = provider_data['claim_amount'].median()
            feature_dict['std_claim_amount'] = provider_data['claim_amount'].std()
            
            # Claims per day
            if 'date_of_service' in provider_data.columns:
                date_range = (provider_data['date_of_service'].max() - 
                            provider_data['date_of_service'].min()).days + 1
                feature_dict['claims_per_day'] = len(provider_data) / max(date_range, 1)
            else:
                feature_dict['claims_per_day'] = 0
            
            # High cost claim ratio
            high_cost_threshold = df['claim_amount'].quantile(0.9)
            feature_dict['high_cost_claim_ratio'] = (
                (provider_data['claim_amount'] > high_cost_threshold).sum() / len(provider_data)
            )
            
            # Procedure diversity
            unique_procedures = provider_data['procedure_code'].nunique()
            feature_dict['unusual_procedure_diversity'] = unique_procedures / len(provider_data)
            
            # Repeated patient ratio
            patient_counts = provider_data['patient_id'].value_counts()
            repeated_patients = (patient_counts > 1).sum()
            feature_dict['repeated_patient_ratio'] = repeated_patients / len(patient_counts)
            
            # Resubmission rate (same patient + procedure within 30 days)
            resubmissions = 0
            if len(provider_data) > 1:
                provider_data_sorted = provider_data.sort_values('date_of_service')
                for i in range(1, len(provider_data_sorted)):
                    current = provider_data_sorted.iloc[i]
                    previous = provider_data_sorted.iloc[i-1]
                    if (current['patient_id'] == previous['patient_id'] and
                        current['procedure_code'] == previous['procedure_code'] and
                        (current['date_of_service'] - previous['date_of_service']).days <= 30):
                        resubmissions += 1
            feature_dict['resubmission_rate'] = resubmissions / len(provider_data)
            
            # Weekend and night claims
            if 'date_of_claim_filed' in provider_data.columns:
                weekend_claims = provider_data['date_of_claim_filed'].dt.weekday.isin([5, 6]).sum()
                feature_dict['weekend_claim_ratio'] = weekend_claims / len(provider_data)
                
                night_claims = provider_data['date_of_claim_filed'].dt.hour.between(0, 5).sum()
                feature_dict['night_claim_ratio'] = night_claims / len(provider_data)
            else:
                feature_dict['weekend_claim_ratio'] = 0
                feature_dict['night_claim_ratio'] = 0
            
            # Time to file
            if ('date_of_service' in provider_data.columns and 
                'date_of_claim_filed' in provider_data.columns):
                time_diffs = (provider_data['date_of_claim_filed'] - 
                            provider_data['date_of_service']).dt.days
                feature_dict['average_time_to_file'] = time_diffs.mean()
            else:
                feature_dict['average_time_to_file'] = 0
            
            # Procedure entropy
            proc_counts = provider_data['procedure_code'].value_counts()
            proc_probs = proc_counts / proc_counts.sum()
            feature_dict['procedure_entropy'] = -np.sum(proc_probs * np.log2(proc_probs + 1e-10))
            
            # Top N procedure share
            top_3_share = proc_counts.head(3).sum() / len(provider_data)
            feature_dict['top_n_procedure_share'] = top_3_share
            
            # Trend analysis (monthly claim count slope)
            if 'date_of_service' in provider_data.columns:
                monthly_counts = provider_data.groupby(
                    provider_data['date_of_service'].dt.to_period('M')
                ).size()
                if len(monthly_counts) > 1:
                    x = np.arange(len(monthly_counts))
                    slope = np.polyfit(x, monthly_counts.values, 1)[0]
                    feature_dict['anomaly_trend_slope'] = slope
                else:
                    feature_dict['anomaly_trend_slope'] = 0
            else:
                feature_dict['anomaly_trend_slope'] = 0
            
            # Add metadata
            if 'specialization' in provider_data.columns:
                feature_dict['specialization'] = provider_data['specialization'].iloc[0]
            else:
                feature_dict['specialization'] = 'Unknown'
                
            if 'region' in provider_data.columns:
                feature_dict['region'] = provider_data['region'].iloc[0]
            else:
                feature_dict['region'] = 'Unknown'
            
            features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    def compute_peer_group_deviations(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Compute peer group z-scores for key metrics.
        
        Validates input and handles gracefully if empty or missing columns.
        """
        logger.info("Computing peer group deviations")
        
        # Validate input
        if features_df is None or len(features_df) == 0:
            logger.warning("Input features_df is empty; returning as-is")
            return features_df if features_df is not None else pd.DataFrame()
        
        # Ensure required columns exist
        if 'specialization' not in features_df.columns:
            logger.warning("specialization column not found; using default 'Unknown'")
            features_df['specialization'] = 'Unknown'
        
        if 'region' not in features_df.columns:
            logger.warning("region column not found; using default 'Unknown'")
            features_df['region'] = 'Unknown'
        
        # Define peer groups
        features_df['peer_group_key'] = (features_df['specialization'].astype(str) + '_' + 
                                       features_df['region'].astype(str))
        
        # Metrics to normalize
        metrics = ['avg_claim_amount', 'total_claims_count', 'high_cost_claim_ratio']
        
        for metric in metrics:
            if metric not in features_df.columns:
                logger.warning(f"Metric {metric} not found in features; skipping normalization")
                continue
            
            peer_stats = features_df.groupby('peer_group_key')[metric].agg(['mean', 'std'])
            
            # Merge back to main dataframe
            features_df = features_df.merge(
                peer_stats.rename(columns={'mean': f'{metric}_peer_mean', 
                                         'std': f'{metric}_peer_std'}),
                left_on='peer_group_key', right_index=True, how='left'
            )
            
            # Compute z-scores
            std_col = f'{metric}_peer_std'
            features_df[std_col] = features_df[std_col].fillna(1)  # Avoid division by zero
            features_df[f'peer_zscore_{metric}'] = (
                (features_df[metric] - features_df[f'{metric}_peer_mean']) / 
                features_df[std_col]
            )
        
        return features_df
    
    def compute_anomaly_score(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Compute weighted anomaly scores and risk categories."""
        logger.info("Computing anomaly scores")
        
        weights = self.config['anomaly_weights']
        
        # Normalize features using tanh
        score_components = []
        
        for feature, weight in weights.items():
            if feature in features_df.columns:
                normalized = np.tanh(features_df[feature].fillna(0))
                score_components.append(weight * normalized)
        
        # Compute weighted sum
        features_df['anomaly_score'] = np.sum(score_components, axis=0)
        
        # Apply sigmoid to get 0-1 range
        features_df['anomaly_score'] = 1 / (1 + np.exp(-features_df['anomaly_score']))
        
        # Assign risk categories
        thresholds = self.config['risk_thresholds']
        features_df['risk_category'] = pd.cut(
            features_df['anomaly_score'],
            bins=[0, thresholds['low'], thresholds['medium'], 1],
            labels=['LOW', 'MEDIUM', 'HIGH'],
            include_lowest=True
        )
        
        # Add timestamp
        features_df['computed_at'] = datetime.now()
        
        return features_df
    
    def generate_fingerprints(self, claims_path: str, output_dir: str = "artifacts") -> Tuple[str, str]:
        """Main method to generate provider fingerprints."""
        logger.info("Starting provider fingerprint generation")
        
        # Load data
        df = self.load_claims_data(claims_path)
        
        # Compute features
        features_df = self.compute_provider_features(df)
        
        # Compute peer deviations
        features_df = self.compute_peer_group_deviations(features_df)
        
        # Compute anomaly scores
        features_df = self.compute_anomaly_score(features_df)
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Try to save parquet; fall back to CSV if pyarrow not available
        parquet_path = Path(output_dir) / "provider_fingerprints.parquet"
        try:
            features_df.to_parquet(parquet_path, index=False)
        except ImportError:
            logger.warning("pyarrow not available; saving as CSV instead")
            parquet_path = Path(output_dir) / "provider_fingerprints.csv"
            features_df.to_csv(parquet_path, index=False)
        
        # Save JSONL with explanations
        jsonl_path = Path(output_dir) / "provider_fingerprints.jsonl"
        self._save_jsonl_with_explanations(features_df, jsonl_path)
        
        logger.info(f"Generated fingerprints for {len(features_df)} providers")
        logger.info(f"Saved to {parquet_path} and {jsonl_path}")
        
        return str(parquet_path), str(jsonl_path)
    
    def _save_jsonl_with_explanations(self, features_df: pd.DataFrame, output_path: Path):
        """Save JSONL with human-readable explanations."""
        with open(output_path, 'w') as f:
            for _, row in features_df.iterrows():
                # Get top contributing features
                feature_scores = {}
                weights = self.config['anomaly_weights']
                
                for feature, weight in weights.items():
                    if feature in row and not pd.isna(row[feature]):
                        feature_scores[feature] = abs(weight * np.tanh(row[feature]))
                
                top_features = sorted(feature_scores.items(), 
                                    key=lambda x: x[1], reverse=True)[:3]
                
                record = {
                    'provider_id': row['provider_id'],
                    'anomaly_score': float(row['anomaly_score']),
                    'risk_category': row['risk_category'],
                    'peer_group': row['peer_group_key'],
                    'top_contributing_features': [
                        {'feature': feat, 'score': float(score)} 
                        for feat, score in top_features
                    ],
                    'summary_stats': {
                        'total_claims': int(row['total_claims_count']),
                        'avg_claim_amount': float(row['avg_claim_amount']),
                        'high_cost_ratio': float(row['high_cost_claim_ratio'])
                    }
                }
                
                f.write(json.dumps(record) + '\n')


def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate provider behavioral fingerprints')
    parser.add_argument('--claims', required=True, help='Path to claims CSV file')
    parser.add_argument('--output', default='artifacts', help='Output directory')
    
    args = parser.parse_args()
    
    generator = ProviderFingerprintGenerator()
    parquet_path, jsonl_path = generator.generate_fingerprints(args.claims, args.output)
    
    print(f"✅ Generated fingerprints:")
    print(f"   Parquet: {parquet_path}")
    print(f"   JSONL: {jsonl_path}")


if __name__ == "__main__":
    main()