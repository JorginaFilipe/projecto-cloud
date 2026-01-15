@echo off
REM Script para executar a aplicacao completa no Windows

echo.
echo ======================================================================
echo     APLICACAO DE ANALISE DE IMAGENS - Google Cloud Vision
echo ======================================================================
echo.

REM Verificar se estamos na pasta correta
if not exist "app.py" (
    echo ERRO: app.py nao encontrado
    echo Certifique-se que esta na pasta projeto_cloud
    pause
    exit /b 1
)

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado
    pause
    exit /b 1
)

REM Instalar dependencias se necessario
echo Verificando dependencias...
pip show google-cloud-vision >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias Python...
    pip install -q -r requirements.txt
    if errorlevel 1 (
        echo ERRO: Falha ao instalar dependencias
        pause
        exit /b 1
    )
)

REM Verificar autenticacao
echo Verificando autenticacao Google Cloud...
gcloud auth list >nul 2>&1
if errorlevel 1 (
    echo.
    echo AVISO: Necessario autenticar com Google Cloud
    echo Executando: gcloud auth application-default login
    gcloud auth application-default login
    if errorlevel 1 (
        echo ERRO: Falha na autenticacao
        pause
        exit /b 1
    )
)

REM Executar aplicacao
echo.
echo ======================================================================
echo     INICIANDO APLICACAO...
echo ======================================================================
echo.
echo 🚀 Aplicacao em execucao!
echo.
echo 📍 Abra no navegador: http://localhost:5000
echo.
echo Funcionalidades:
echo   - Upload de imagens (drag & drop)
echo   - Analise com Vision API
echo   - Armazenamento em Firestore
echo   - Visualizacao de resultados
echo.
echo Pressione Ctrl+C para parar
echo.
echo ======================================================================
echo.

python app.py

pause
