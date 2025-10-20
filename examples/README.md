# Exemplos de Uso da Feature Store

Esta pasta contém exemplos práticos de como usar a Feature Store Architecture em diferentes cenários.

## 📋 Lista de Exemplos

### 1. Basic Usage (`basic_usage.py`)

Exemplo básico demonstrando os conceitos fundamentais:
- Inicialização da Feature Store
- Criação de Feature Groups
- Registro de features
- Ingestão de dados
- Busca de features online e offline

**Execute:**
```bash
python examples/basic_usage.py
```

**Pré-requisitos:**
- Redis rodando na porta 6379

### 2. Advanced Transformations (`advanced_transformations.py`)

Exemplo avançado mostrando transformações complexas:
- Features derivadas com transformações customizadas
- Validações avançadas
- Cálculo de métricas complexas (CLV, scores)
- Features que dependem de outras features

**Execute:**
```bash
python examples/advanced_transformations.py
```

**Conceitos Demonstrados:**
- `FeatureTransformation` com funções lambda
- `FeatureTransformation` com funções customizadas
- `FeatureValidation` com ranges e constraints
- Computação automática de features derivadas

### 3. API Usage (`api_usage.py`)

Exemplo de integração com a API REST:
- Health checks
- Ingestão de features via POST
- Busca de features via GET
- Filtros de features específicas
- Busca de metadados
- Simulação de uso em produção

**Execute:**

Terminal 1 (Servidor):
```bash
python src/feature_serving_api.py
```

Terminal 2 (Cliente):
```bash
python examples/api_usage.py
```

**Endpoints Demonstrados:**
- `GET /health` - Health check
- `GET /groups` - Listar feature groups
- `POST /ingest/{group}/{entity}` - Ingerir features
- `GET /features/{group}/{entity}` - Buscar features
- `GET /features?features=x,y` - Buscar features específicas
- `GET /features` - Listar todas as features
- `GET /features/{entity}/{name}/metadata` - Metadados

## 🚀 Quick Start

### Pré-requisitos Gerais

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Iniciar Redis:**
```bash
# Opção 1: Docker (recomendado)
docker run --name feature-store-redis -p 6379:6379 -d redis/redis-stack-server:latest

# Opção 2: Local
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# macOS
brew install redis
brew services start redis
```

3. **Verificar Redis:**
```bash
redis-cli ping
# Deve retornar: PONG
```

### Executando Todos os Exemplos

```bash
# 1. Exemplo básico
python examples/basic_usage.py

# 2. Transformações avançadas
python examples/advanced_transformations.py

# 3. API (precisa de 2 terminais)
# Terminal 1:
python src/feature_serving_api.py

# Terminal 2:
python examples/api_usage.py
```

## 📂 Estrutura de Dados Gerada

Os exemplos criam a seguinte estrutura de dados:

```
data/
└── examples/
    ├── basic_offline/          # Dados do exemplo básico
    │   └── customer_metrics/
    │       └── date=YYYY-MM-DD/
    │           └── data.parquet
    └── advanced_offline/       # Dados do exemplo avançado
        └── customer_advanced/
            └── date=YYYY-MM-DD/
                └── data.parquet
```

## 🎓 Conceitos por Exemplo

### Basic Usage
- ✅ Inicialização da Feature Store
- ✅ Criação de Feature Groups
- ✅ Registro de features básicas
- ✅ Ingestão de dados simples
- ✅ Busca online (Redis)
- ✅ Busca offline (Parquet)
- ✅ Listagem de features

### Advanced Transformations
- ✅ Transformações com lambda functions
- ✅ Transformações com funções customizadas
- ✅ Validações de ranges e constraints
- ✅ Features derivadas calculadas automaticamente
- ✅ Análise de perfis de clientes
- ✅ Cálculos de métricas complexas (CLV, recency)

### API Usage
- ✅ Integração via HTTP/REST
- ✅ Ingestão via POST
- ✅ Busca via GET
- ✅ Filtros e parâmetros de query
- ✅ Listagem e discovery de features
- ✅ Acesso a metadados
- ✅ Padrão de uso em produção
- ✅ Medição de latência

## 🐛 Troubleshooting

### Erro: Connection Refused (Redis)

**Problema:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solução:**
```bash
# Verificar se Redis está rodando
redis-cli ping

# Se não estiver, inicie:
docker start feature-store-redis
# ou
sudo systemctl start redis-server
```

### Erro: ModuleNotFoundError

**Problema:** `ModuleNotFoundError: No module named 'feature_store'`

**Solução:**
```bash
# Certifique-se de estar no diretório raiz do projeto
cd /path/to/feature-store-architecture

# Execute os exemplos a partir do diretório raiz
python examples/basic_usage.py
```

### API não responde

**Problema:** Exemplo `api_usage.py` não consegue conectar

**Solução:**
1. Certifique-se de que o servidor está rodando:
   ```bash
   python src/feature_serving_api.py
   ```
2. Verifique se a porta 5000 não está em uso:
   ```bash
   lsof -i :5000  # Linux/macOS
   netstat -ano | findstr :5000  # Windows
   ```
3. Se necessário, altere a porta em `feature_serving_api.py`

### Dados offline não aparecem

**Problema:** `get_offline_features()` retorna None ou vazio

**Causas possíveis:**
1. Dados foram ingeridos mas não no range de datas buscado
2. Particionamento por data está incorreto
3. Permissões de arquivo

**Solução:**
```python
# Buscar com range amplo
from datetime import datetime, timedelta
offline = fs.get_offline_features(
    "group_name",
    start_date=datetime(2020, 1, 1),
    end_date=datetime.now() + timedelta(days=1)
)
```

## 📚 Próximos Passos

Após executar os exemplos:

1. **Leia a documentação:**
   - [Getting Started Guide](../docs/GETTING_STARTED.md)
   - [Architecture Documentation](../docs/ARCHITECTURE.md)
   - [Best Practices](../docs/BEST_PRACTICES.md)

2. **Explore o código:**
   - [`src/feature_store.py`](../src/feature_store.py) - Implementação principal
   - [`src/feature_serving_api.py`](../src/feature_serving_api.py) - API REST

3. **Execute os testes:**
   ```bash
   pytest tests/ -v
   ```

4. **Crie seus próprios exemplos:**
   - Adapte os exemplos para seus casos de uso
   - Experimente com diferentes tipos de features
   - Teste com seus próprios dados

## 💡 Dicas

- **Use variáveis de ambiente** para configurações (veja `config/.env.example`)
- **Comece simples** com o exemplo básico antes de avançar
- **Monitore o Redis** para entender o impacto no armazenamento
- **Experimente com diferentes transformações** para ver o que funciona melhor
- **Use tags** para organizar suas features desde o início
- **Documente suas features** com descrições claras

## 🤝 Contribuindo

Tem um exemplo interessante? Contribua!

1. Crie um novo arquivo de exemplo
2. Documente claramente o que demonstra
3. Adicione à lista acima
4. Teste para garantir que funciona
5. Envie um Pull Request

## 📞 Suporte

- **Issues:** [GitHub Issues](https://github.com/galafis/feature-store-architecture/issues)
- **Documentação:** [docs/](../docs/)
- **Código-fonte:** [src/](../src/)
