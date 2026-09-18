PROJETO: MICROSSERVIÇO DE MARKETING COM INTELIGÊNCIA ARTIFICIAL

1. SOBRE O PROJETO
Microsserviço construído com FastAPI e a API do Google Gemini para criar textos automáticos de vendas para o varejo. O sistema gera conteúdos para Instagram, WhatsApp e E-commerce, garantindo respostas estruturadas e sistema de memória rápida (cache).

2. TECNOLOGIAS UTILIZADAS
- Linguagem: Python
- Framework Web: FastAPI
- Servidor: Uvicorn
- Validação de dados: Pydantic
- Inteligência Artificial: Google Gemini
- Banco rápido: Cache em memória RAM via chave SHA-256

3. COMO EXECUTAR O SISTEMA
- Ativar o ambiente virtual:
  .\venv\Scripts\Activate.ps1

- Instalar as dependências:
  pip install -r requirements.txt

- Iniciar a API:
  uvicorn main:app --reload

4. ENDPOINTS DA API
- POST /v1/generate-copy: Envia as informações do produto e recebe os textos para cada rede social.
- GET /health: Informa se a API está funcionando e a quantidade de itens salvos na memória.

5. SCRIPTS DE TESTE
- python benchmark.py: Testa a velocidade do sistema e a economia de tempo com o cache em memória.
- python test_falhas.py: Testa se o sistema bloqueia envios com dados incompletos usando o erro HTTP 422.