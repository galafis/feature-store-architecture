"""
Feature Serving API - REST API for serving features in real-time
Author: Gabriel Demetrios Lafis
Year: 2025

API RESTful construída com Flask para servir features em tempo real.
"""

from flask import Flask, jsonify, request
from feature_store import FeatureStore
from datetime import datetime
import os

# Configuração da Feature Store
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
OFFLINE_STORE_PATH = os.environ.get('OFFLINE_STORE_PATH', './data/offline_store')

def create_app(feature_store: FeatureStore = None):
    """
    Cria e configura a aplicação Flask.
    
    Args:
        feature_store: Instância da FeatureStore (opcional, cria uma nova se não fornecida)
    
    Returns:
        Aplicação Flask configurada
    """
    app = Flask(__name__)
    
    if feature_store is None:
        feature_store = FeatureStore(
            name="production-feature-store",
            redis_host=REDIS_HOST,
            redis_port=REDIS_PORT,
            offline_store_path=OFFLINE_STORE_PATH
        )
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "feature-serving-api",
            "timestamp": datetime.now().isoformat()
        })
    
    @app.route('/features/<group_name>/<entity_id>', methods=['GET'])
    def get_features(group_name, entity_id):
        """
        Retorna features online para uma entidade específica.
        
        Query params:
            features (opcional): Lista de features específicas separadas por vírgula
        """
        # Verificar se o grupo existe
        if group_name not in feature_store.feature_groups:
            return jsonify({
                "error": f"Feature group '{group_name}' not found"
            }), 404
        
        features = feature_store.get_online_features(group_name, entity_id)
        
        if not features:
            return jsonify({
                "error": "Features not found",
                "group_name": group_name,
                "entity_id": entity_id
            }), 404
        
        # Filtrar features específicas se solicitado
        requested_features = request.args.get('features')
        if requested_features:
            requested_list = [f.strip() for f in requested_features.split(',')]
            features = {k: v for k, v in features.items() if k in requested_list}
        
        return jsonify(features)
    
    @app.route('/ingest/<group_name>/<entity_id>', methods=['POST'])
    def ingest(group_name, entity_id):
        """
        Ingere dados e computa features.
        
        Body (JSON): Dados brutos para computar as features
        """
        # Verificar se o grupo existe
        if group_name not in feature_store.feature_groups:
            return jsonify({
                "error": f"Feature group '{group_name}' not found"
            }), 404
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        try:
            feature_store.ingest_features(group_name, entity_id, data)
            return jsonify({
                "status": "success",
                "group_name": group_name,
                "entity_id": entity_id
            }), 201
        except ValueError as e:
            return jsonify({
                "error": f"Validation failed: {str(e)}"
            }), 400
        except Exception as e:
            return jsonify({
                "error": f"Internal server error: {str(e)}"
            }), 500
    
    @app.route('/groups', methods=['GET'])
    def list_groups():
        """Lista todos os feature groups registrados"""
        groups = []
        for name, group in feature_store.feature_groups.items():
            groups.append({
                "name": name,
                "entity": group.entity,
                "description": group.description,
                "num_features": len(group.features),
                "created_at": group.created_at.isoformat()
            })
        return jsonify({"groups": groups})
    
    @app.route('/features', methods=['GET'])
    def list_all_features():
        """Lista todas as features registradas"""
        features_list = []
        for metadata in feature_store.list_features():
            features_list.append({
                "name": metadata.name,
                "description": metadata.description,
                "type": metadata.feature_type.value,
                "entity": metadata.entity,
                "status": metadata.status.value,
                "owner": metadata.owner,
                "tags": metadata.tags,
                "version": metadata.version
            })
        return jsonify({"features": features_list})
    
    @app.route('/features/<entity>/<feature_name>/metadata', methods=['GET'])
    def get_feature_info(entity, feature_name):
        """Retorna metadados de uma feature específica"""
        metadata = feature_store.get_feature_metadata(feature_name, entity)
        if not metadata:
            return jsonify({
                "error": f"Feature '{feature_name}' not found for entity '{entity}'"
            }), 404
        
        return jsonify({
            "name": metadata.name,
            "description": metadata.description,
            "type": metadata.feature_type.value,
            "entity": metadata.entity,
            "status": metadata.status.value,
            "owner": metadata.owner,
            "tags": metadata.tags,
            "version": metadata.version,
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat()
        })
    
    return app


if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*60)
    print("Feature Serving API")
    print("="*60)
    print(f"Starting server on http://0.0.0.0:5000")
    print("\nAvailable endpoints:")
    print("  GET  /health")
    print("  GET  /groups")
    print("  GET  /features")
    print("  GET  /features/<group_name>/<entity_id>")
    print("  POST /ingest/<group_name>/<entity_id>")
    print("  GET  /features/<entity>/<feature_name>/metadata")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
