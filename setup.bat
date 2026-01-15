@echo off
REM Script batch para começar rapidamente no Windows

echo.
echo ======================================================================
echo     Configuracao Rapida - Processamento de Imagens Google Cloud
echo ======================================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Instale Python 3.7+
    exit /b 1
)
echo [OK] Python instalado

REM Verificar gcloud
gcloud --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: gcloud CLI nao encontrado. Instale Google Cloud SDK
    exit /b 1
)
echo [OK] gcloud CLI instalado

REM Criar ambiente virtual
if not exist venv (
    echo.
    echo Criando ambiente virtual...
    python -m venv venv
    echo [OK] Ambiente virtual criado
)

REM Ativar ambiente virtual
call venv\Scripts\activate.bat
echo [OK] Ambiente virtual ativado

REM Instalar dependencias
echo.
echo Instalando dependencias Python...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias
    exit /b 1
)
echo [OK] Dependencias instaladas

REM Verificar autenticacao
echo.
echo Verificando autenticacao Google Cloud...
gcloud auth list >nul 2>&1
if errorlevel 1 (
    echo AVISO: Precisa autenticar
    echo Executando: gcloud auth application-default login
    gcloud auth application-default login
)
echo [OK] Autenticado

echo.
echo ======================================================================
echo     Configuracao Completa!
echo ======================================================================
echo.
echo Proximos passos:
echo.
echo 1. Abra 3 terminais PowerShell
echo.
echo    Terminal 1 - API de Upload:
echo    python upload_api.py
echo.
echo    Terminal 2 - API de Resultados:
echo    python api_resultados.py
echo.
echo    Terminal 3 - Subscriber de Notificacoes (opcional):
echo    python notificacoes.py
echo.
echo 2. Abra seu navegador em: http://localhost:8000
echo.
echo 3. Para testes via CLI:
echo    python test_api.py
echo.
echo Documentacao:
echo - QUICKSTART.md - Guia rapido
echo - SETUP_GUIDE.md - Instalacao detalhada
echo - ARCHITECTURE.md - Arquitetura do sistema
echo.
echo ======================================================================
echo.
pause
