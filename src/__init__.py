"""
Feature Store Architecture Package
Author: Gabriel Demetrios Lafis
Year: 2025
"""

from .feature_store import (
    FeatureStore,
    Feature,
    FeatureMetadata,
    FeatureType,
    FeatureStatus,
    FeatureValidation,
    FeatureTransformation,
    FeatureGroup
)

__all__ = [
    'FeatureStore',
    'Feature',
    'FeatureMetadata',
    'FeatureType',
    'FeatureStatus',
    'FeatureValidation',
    'FeatureTransformation',
    'FeatureGroup'
]

__version__ = '1.0.0'
