# Getting Started with Feature Store Architecture

Este guia fornece uma introdução completa para começar a usar a Feature Store Architecture.

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.9+**: A linguagem de programação principal
- **pip**: Gerenciador de pacotes Python
- **Docker** (opcional): Para executar o Redis facilmente
- **Git**: Para clonar o repositório

## 🚀 Instalação

### 1. Clone o Repositório

```bash
git clone https://github.com/galafis/feature-store-architecture.git
cd feature-store-architecture
```

### 2. Crie um Ambiente Virtual (Recomendado)

```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o Redis

#### Opção A: Usando Docker (Recomendado)

```bash
docker run --name feature-store-redis -p 6379:6379 -d redis/redis-stack-server:latest
```

#### Opção B: Instalação Local

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**macOS (com Homebrew):**
```bash
brew install redis
brew services start redis
```

**Windows:**
Baixe e instale o Redis do repositório oficial ou use o WSL2.

## 🎯 Primeiro Exemplo: Feature Store Básica

Crie um arquivo `exemplo_basico.py`:

```python
from src.feature_store import (
    FeatureStore,
    FeatureMetadata,
    FeatureType,
    FeatureStatus,
    FeatureGroup
)
from datetime import datetime

# 1. Inicializar a Feature Store
fs = FeatureStore(
    name="my-first-feature-store",
    redis_host="localhost",
    redis_port=6379,
    offline_store_path="./data/offline_store"
)

# 2. Criar um Feature Group
customer_fg = FeatureGroup(
    name="customer_metrics",
    entity="customer",
    description="Métricas básicas de clientes",
    features=[
        FeatureMetadata(
            name="total_purchases",
            description="Total de compras realizadas",
            feature_type=FeatureType.NUMERICAL,
            entity="customer",
            owner="analytics-team@example.com",
            tags=["customer", "purchases"],
            status=FeatureStatus.ACTIVE
        ),
        FeatureMetadata(
            name="customer_lifetime_value",
            description="Valor total gasto pelo cliente",
            feature_type=FeatureType.NUMERICAL,
            entity="customer",
            owner="analytics-team@example.com",
            tags=["customer", "revenue"],
            status=FeatureStatus.ACTIVE
        )
    ]
)

# 3. Registrar o Feature Group
fs.register_feature_group(customer_fg)

# 4. Ingerir dados
customer_data = {
    "total_purchases": 10,
    "customer_lifetime_value": 1250.50
}
fs.ingest_features("customer_metrics", "CUST001", customer_data)

# 5. Buscar features online (para inferência)
online_features = fs.get_online_features("customer_metrics", "CUST001")
print("Features Online:", online_features)

# 6. Buscar features offline (para treinamento)
offline_features = fs.get_offline_features("customer_metrics")
print("Features Offline:")
print(offline_features)

# 7. Listar todas as features
all_features = fs.list_features()
for feature in all_features:
    print(f"- {feature.name} ({feature.feature_type.value}): {feature.description}")
```

Execute:
```bash
python exemplo_basico.py
```

## 🔧 Exemplo com Transformações

```python
from src.feature_store import (
    FeatureStore,
    FeatureMetadata,
    FeatureType,
    FeatureStatus,
    FeatureTransformation,
    FeatureValidation,
    FeatureGroup
)

fs = FeatureStore(name="advanced-feature-store")

# Feature com transformação
customer_fg = FeatureGroup(
    name="customer_advanced",
    entity="customer",
    description="Features avançadas de clientes",
    features=[
        FeatureMetadata(
            name="avg_purchase_value",
            description="Valor médio por compra",
            feature_type=FeatureType.NUMERICAL,
            entity="customer",
            owner="analytics-team@example.com",
            transformation=FeatureTransformation(
                name="calculate_average",
                description="Calcula valor médio",
                source_features=["total_spent", "total_purchases"],
                transformation_fn=lambda data: (
                    data["total_spent"] / data["total_purchases"]
                    if data["total_purchases"] > 0 else 0
                )
            ),
            validation=FeatureValidation(min_value=0, max_value=10000)
        )
    ]
)

fs.register_feature_group(customer_fg)

# Ingerir dados brutos - a transformação é aplicada automaticamente
raw_data = {
    "total_spent": 5000.0,
    "total_purchases": 10
}
fs.ingest_features("customer_advanced", "CUST002", raw_data)

features = fs.get_online_features("customer_advanced", "CUST002")
print(f"Valor médio por compra: {features['avg_purchase_value']}")
```

## 🌐 Exemplo com API REST

### 1. Inicie o Servidor da API

```bash
python src/feature_serving_api.py
```

Ou usando código Python:

```python
from src.feature_serving_api import create_app

app = create_app()
app.run(host='0.0.0.0', port=5000)
```

### 2. Use a API

**Buscar Features:**
```bash
curl http://localhost:5000/features/customer_metrics/CUST001
```

**Ingerir Features:**
```bash
curl -X POST http://localhost:5000/ingest/customer_metrics/CUST001 \
  -H "Content-Type: application/json" \
  -d '{"total_purchases": 15, "customer_lifetime_value": 2000.00}'
```

**Listar Feature Groups:**
```bash
curl http://localhost:5000/groups
```

**Health Check:**
```bash
curl http://localhost:5000/health
```

## 📊 Gerando Dados de Exemplo

Execute o módulo de exemplos do mundo real:

```bash
python src/real_world_examples.py
```

Isso gerará datasets de exemplo em `data/examples/`:
- `ecommerce_customers.parquet`
- `ecommerce_products.parquet`
- `ecommerce_interactions.parquet`
- `financial_transactions.parquet`

## 🧪 Executando Testes

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ -v --cov=src --cov-report=html

# Teste específico
pytest tests/test_feature_store.py::TestFeatureStore::test_ingest_data_online_store -v
```

## 📁 Estrutura de Diretórios Criada

Após a instalação e execução dos exemplos, você terá:

```
feature-store-architecture/
├── data/
│   ├── examples/           # Datasets de exemplo
│   └── offline_store/      # Armazenamento offline (Parquet)
├── src/
│   ├── feature_store.py    # Implementação principal
│   └── feature_serving_api.py  # API REST
├── tests/                  # Testes unitários e de integração
├── docs/                   # Documentação adicional
└── config/                 # Arquivos de configuração
```

## 🐛 Solução de Problemas

### Redis Connection Error

**Problema:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solução:**
- Verifique se o Redis está rodando: `redis-cli ping` (deve retornar "PONG")
- Verifique a porta: `sudo lsof -i :6379`
- Reinicie o Redis: `sudo systemctl restart redis-server` (Linux) ou `brew services restart redis` (macOS)

### Import Error

**Problema:** `ModuleNotFoundError: No module named 'redis'`

**Solução:**
```bash
pip install -r requirements.txt
```

### Permission Error ao Criar Diretórios

**Problema:** `PermissionError: [Errno 13] Permission denied: './data'`

**Solução:**
- Execute com permissões adequadas ou
- Altere o caminho do offline_store para um diretório onde você tem permissões:
```python
fs = FeatureStore(name="my-fs", offline_store_path="~/feature-store-data")
```

## 📚 Próximos Passos

1. Leia sobre [Arquitetura e Design Patterns](ARCHITECTURE.md)
2. Veja [Best Practices](BEST_PRACTICES.md)
3. Explore os [Exemplos práticos](../examples/)

## 💡 Dicas

- **Use variáveis de ambiente** para configurações sensíveis (host, porta, credenciais)
- **Monitore o uso do Redis** com `redis-cli info memory`
- **Configure backups** para o armazenamento offline (Parquet)
- **Use feature versioning** para rastreabilidade
- **Documente suas features** com descrições claras e tags apropriadas
- **Valide features** com `FeatureValidation` para garantir qualidade dos dados

## 🤝 Suporte

- **Issues:** [GitHub Issues](https://github.com/galafis/feature-store-architecture/issues)
- **Documentação:** [docs/](.)
- **Exemplos:** [examples/](../examples/)
