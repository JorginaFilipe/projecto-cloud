"""
Exemplos de testes para o fluxo de processamento de imagens
"""

import requests
import json
from datetime import datetime

# Configurações
BASE_URL_UPLOAD = "http://localhost:5000"
BASE_URL_RESULTADOS = "http://localhost:5001"

# Cores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(texto):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{texto}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(texto):
    print(f"{Colors.OKGREEN}✅ {texto}{Colors.ENDC}")


def print_info(texto):
    print(f"{Colors.OKCYAN}ℹ️  {texto}{Colors.ENDC}")


def print_error(texto):
    print(f"{Colors.FAIL}❌ {texto}{Colors.ENDC}")


def print_warning(texto):
    print(f"{Colors.WARNING}⚠️  {texto}{Colors.ENDC}")


# ============================================================================
# TESTE 1: Health Check
# ============================================================================

def teste_health_check():
    print_header("TESTE 1: Health Check")
    
    try:
        print_info("Verificando API de Upload...")
        response = requests.get(f"{BASE_URL_UPLOAD}/health")
        if response.status_code == 200:
            print_success("API de Upload está operacional")
        else:
            print_error(f"Status inesperado: {response.status_code}")
            
        print_info("Verificando API de Resultados...")
        response = requests.get(f"{BASE_URL_RESULTADOS}/health")
        if response.status_code == 200:
            print_success("API de Resultados está operacional")
        else:
            print_error(f"Status inesperado: {response.status_code}")
            
    except Exception as e:
        print_error(f"Erro ao conectar: {e}")
        print_warning("Certifique-se de que as APIs estão em execução:")
        print("  Terminal 1: python upload_api.py")
        print("  Terminal 2: python api_resultados.py")


# ============================================================================
# TESTE 2: Listar Resultados Existentes
# ============================================================================

def teste_listar_resultados():
    print_header("TESTE 2: Listar Resultados Existentes")
    
    try:
        print_info("Consultando resultados do Firestore...")
        response = requests.get(f"{BASE_URL_RESULTADOS}/resultados?limit=5")
        
        if response.status_code == 200:
            dados = response.json()
            print_success(f"Total de análises: {dados.get('total', 0)}")
            
            if dados.get('resultados'):
                for i, resultado in enumerate(dados['resultados'], 1):
                    print(f"\n  {i}. Arquivo: {resultado['nome_arquivo']}")
                    print(f"     ID: {resultado['id']}")
                    print(f"     Labels: {resultado['total_labels']}")
                    print(f"     Textos: {resultado['total_textos']}")
                    print(f"     Rostos: {resultado['total_rostos']}")
            else:
                print_warning("Nenhuma análise realizada ainda")
        else:
            print_error(f"Erro: Status {response.status_code}")
            
    except Exception as e:
        print_error(f"Erro ao listar resultados: {e}")


# ============================================================================
# TESTE 3: Consultar Resultado Específico
# ============================================================================

def teste_consultar_resultado(doc_id):
    print_header(f"TESTE 3: Consultar Resultado Específico ({doc_id})")
    
    try:
        print_info(f"Consultando documento {doc_id}...")
        response = requests.get(f"{BASE_URL_RESULTADOS}/resultados/{doc_id}")
        
        if response.status_code == 200:
            resultado = response.json()
            print_success("Resultado encontrado!")
            print(f"\nArquivo: {resultado['nome_arquivo']}")
            print(f"Status: {resultado['status']}")
            print(f"\nResultados:")
            print(f"  - Labels: {resultado['total_labels']}")
            print(f"  - Textos: {resultado['total_textos']}")
            print(f"  - Rostos: {resultado['total_rostos']}")
            
            # Mostrar os 3 principais labels
            if resultado['resultados'].get('labels'):
                print("\n  Top 3 Labels:")
                for i, label in enumerate(resultado['resultados']['labels'][:3], 1):
                    print(f"    {i}. {label['descricao']} ({label['score']*100:.1f}%)")
                    
        elif response.status_code == 404:
            print_error("Documento não encontrado")
        else:
            print_error(f"Erro: Status {response.status_code}")
            
    except Exception as e:
        print_error(f"Erro ao consultar: {e}")


# ============================================================================
# TESTE 4: Buscar por Nome de Arquivo
# ============================================================================

def teste_buscar_por_nome(nome):
    print_header(f"TESTE 4: Buscar por Nome ({nome})")
    
    try:
        print_info(f"Buscando análises com '{nome}'...")
        response = requests.get(
            f"{BASE_URL_RESULTADOS}/resultados/search",
            params={'nome': nome, 'limit': 5}
        )
        
        if response.status_code == 200:
            dados = response.json()
            print_success(f"Encontrados {dados.get('total', 0)} resultados")
            
            for resultado in dados.get('resultados', []):
                print(f"\n  {resultado['nome_arquivo']}")
                print(f"    ID: {resultado['id']}")
                
        else:
            print_error(f"Erro: Status {response.status_code}")
            
    except Exception as e:
        print_error(f"Erro ao buscar: {e}")


# ============================================================================
# TESTE 5: Obter Labels de Uma Análise
# ============================================================================

def teste_obter_labels(doc_id):
    print_header(f"TESTE 5: Obter Labels ({doc_id})")
    
    try:
        print_info("Consultando labels detectados...")
        response = requests.get(f"{BASE_URL_RESULTADOS}/resultados/{doc_id}/labels")
        
        if response.status_code == 200:
            dados = response.json()
            print_success(f"Total de labels: {dados['total_labels']}")
            
            print("\nLabels (por ordem de confiança):")
            for i, label in enumerate(dados['labels'][:10], 1):
                score = label['score'] * 100
                barra = "█" * int(score / 5) + "░" * (20 - int(score / 5))
                print(f"  {i:2d}. {label['descricao']:30s} {barra} {score:5.1f}%")
                
        else:
            print_error(f"Erro: Status {response.status_code}")
            
    except Exception as e:
        print_error(f"Erro ao obter labels: {e}")


# ============================================================================
# TESTE 6: Obter Texto Detectado (OCR)
# ============================================================================

def teste_obter_texto(doc_id):
    print_header(f"TESTE 6: Obter Texto (OCR) ({doc_id})")
    
    try:
        print_info("Consultando texto detectado...")
        response = requests.get(f"{BASE_URL_RESULTADOS}/resultados/{doc_id}/texto")
        
        if response.status_code == 200:
            dados = response.json()
            
            if dados['texto_completo']:
                print_success("Texto detectado!")
                print(f"\n{Colors.BOLD}Texto Completo:{Colors.ENDC}")
                print(dados['texto_completo'])
            else:
                print_warning("Nenhum texto detectado na imagem")
                
        else:
            print_error(f"Erro: Status {response.status_code}")
            
    except Exception as e:
        print_error(f"Erro ao obter texto: {e}")


# ============================================================================
# TESTE 7: Obter Rostos Detectados
# ============================================================================

def teste_obter_rostos(doc_id):
    print_header(f"TESTE 7: Obter Rostos ({doc_id})")
    
    try:
        print_info("Consultando rostos detectados...")
        response = requests.get(f"{BASE_URL_RESULTADOS}/resultados/{doc_id}/rostos")
        
        if response.status_code == 200:
            dados = response.json()
            
            if dados['total_rostos'] > 0:
                print_success(f"Total de rostos: {dados['total_rostos']}")
                
                for i, rosto in enumerate(dados['rostos'], 1):
                    print(f"\n  Rosto {i}:")
                    print(f"    Confiança: {rosto['confianca']*100:.1f}%")
                    print(f"    Alegria: {rosto['alegria']}/10")
                    print(f"    Surpresa: {rosto['surpresa']}/10")
            else:
                print_warning("Nenhum rosto detectado")
                
        else:
            print_error(f"Erro: Status {response.status_code}")
            
    except Exception as e:
        print_error(f"Erro ao obter rostos: {e}")


# ============================================================================
# TESTE 8: Obter Análise de Segurança
# ============================================================================

def teste_obter_safe_search(doc_id):
    print_header(f"TESTE 8: Análise de Segurança ({doc_id})")
    
    try:
        print_info("Consultando análise de segurança...")
        response = requests.get(f"{BASE_URL_RESULTADOS}/resultados/{doc_id}/safe-search")
        
        if response.status_code == 200:
            dados = response.json()
            safe = dados['safe_search']
            
            print_success("Análise concluída!")
            print(f"\n  Conteúdo Adulto: {Colors.BOLD}{safe['adulto']}{Colors.ENDC}")
            print(f"  Violência: {Colors.BOLD}{safe['violencia']}{Colors.ENDC}")
            print(f"  Spam: {Colors.BOLD}{safe['spam']}{Colors.ENDC}")
            if 'conteudo_medico' in safe:
                print(f"  Médico: {Colors.BOLD}{safe['conteudo_medico']}{Colors.ENDC}")
                
        else:
            print_error(f"Erro: Status {response.status_code}")
            
    except Exception as e:
        print_error(f"Erro ao obter análise: {e}")


# ============================================================================
# MENU INTERATIVO
# ============================================================================

def menu_principal():
    print_header("TESTE DE API - Análise de Imagens")
    
    while True:
        print(f"""
{Colors.BOLD}Menu de Testes:{Colors.ENDC}
  1. Health Check
  2. Listar Resultados
  3. Consultar Resultado Específico
  4. Buscar por Nome de Arquivo
  5. Obter Labels
  6. Obter Texto (OCR)
  7. Obter Rostos
  8. Obter Análise de Segurança
  0. Sair
        """)
        
        opcao = input(f"{Colors.BOLD}Escolha uma opção: {Colors.ENDC}").strip()
        
        if opcao == "1":
            teste_health_check()
            
        elif opcao == "2":
            teste_listar_resultados()
            
        elif opcao == "3":
            doc_id = input("Introduza o ID do documento: ").strip()
            if doc_id:
                teste_consultar_resultado(doc_id)
            else:
                print_error("ID inválido")
                
        elif opcao == "4":
            nome = input("Introduza o nome a buscar: ").strip()
            if nome:
                teste_buscar_por_nome(nome)
            else:
                print_error("Nome inválido")
                
        elif opcao == "5":
            doc_id = input("Introduza o ID do documento: ").strip()
            if doc_id:
                teste_obter_labels(doc_id)
            else:
                print_error("ID inválido")
                
        elif opcao == "6":
            doc_id = input("Introduza o ID do documento: ").strip()
            if doc_id:
                teste_obter_texto(doc_id)
            else:
                print_error("ID inválido")
                
        elif opcao == "7":
            doc_id = input("Introduza o ID do documento: ").strip()
            if doc_id:
                teste_obter_rostos(doc_id)
            else:
                print_error("ID inválido")
                
        elif opcao == "8":
            doc_id = input("Introduza o ID do documento: ").strip()
            if doc_id:
                teste_obter_safe_search(doc_id)
            else:
                print_error("ID inválido")
                
        elif opcao == "0":
            print_success("Até logo!")
            break
            
        else:
            print_error("Opção inválida")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    menu_principal()
