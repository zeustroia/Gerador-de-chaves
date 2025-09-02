import hashlib
import base58
import bech32
import requests
import random
from ecdsa import SECP256k1, SigningKey
from colorama import init, Fore, Style

# --- FUNÇÕES AUXILIARES ---

def verificar_saldo(endereco, tipo_endereco):
    """Verifica o saldo de um endereço Bitcoin usando a API do blockstream.info."""
    try:
        url = f"https://blockstream.info/api/address/{endereco}"
        response = requests.get(url, timeout=10) # Aumentado o timeout para 10s
        response.raise_for_status()
        dados = response.json()
        saldo_satoshi = dados['chain_stats']['funded_txo_sum'] - dados['chain_stats']['spent_txo_sum']
        saldo_btc = saldo_satoshi / 100_000_000.0
        
        cor_saldo = Fore.GREEN if saldo_btc > 0 else Fore.WHITE
        print(f"{cor_saldo}Saldo ({tipo_endereco}): {saldo_btc:.8f} BTC")
    except requests.exceptions.HTTPError:
        print(f"Saldo ({tipo_endereco}): 0.00000000 BTC (Endereço nunca utilizado)")
    except requests.exceptions.RequestException:
        print(f"{Fore.RED}Erro de conexão ao verificar saldo ({tipo_endereco}). Verifique sua internet.")
    except Exception as e:
        print(f"{Fore.RED}Ocorreu um erro inesperado ao verificar saldo ({tipo_endereco}): {e}")

def gerar_comando_keyhunt_opcional(range_gerado):
    """
    Função auxiliar que pergunta se o usuário quer gerar o comando para o keyhunt
    e o monta de forma inteligente.
    """
    try:
        escolha = input(f"\n{Style.BRIGHT}Deseja criar a linha de comando completa para o keyhunt? (s/n): {Style.NORMAL}").strip().lower()
        if escolha == 's':
            nome_arquivo = input(f"{Style.BRIGHT}Qual o nome do arquivo para o endereço (sem a extensão .txt)? {Style.NORMAL}").strip()
            
            # Lógica inteligente para adicionar .txt
            if nome_arquivo.lower().endswith('.txt'):
                nome_arquivo_final = nome_arquivo
            else:
                nome_arquivo_final = f"{nome_arquivo}.txt"

            comando = f"./keyhunt -m address -f tests/{nome_arquivo_final} -r {range_gerado} -l compress"
            
            print(f"\n{Fore.CYAN}---------------------------------------------")
            print(f"{Style.BRIGHT}Comando para Keyhunt (copie e cole):{Style.NORMAL}")
            print(comando)
            print(f"{Fore.CYAN}---------------------------------------------")
            
    except Exception as e:
        print(f"\n{Fore.RED}Ocorreu um erro ao gerar o comando: {e}")

# --- FUNÇÕES PRINCIPAIS DO MENU ---

def gerar_chave(numero):
    """Gera a chave e todos os seus derivados, e verifica o saldo."""
    try:
        chave_privada_bytes = numero.to_bytes(32, 'big')
        chave_privada_hex = chave_privada_bytes.hex()
        sk = SigningKey.from_string(chave_privada_bytes, curve=SECP256k1)
        vk = sk.get_verifying_key()
        chave_publica_comprimida = vk.to_string("compressed")
        sha256_bpk = hashlib.sha256(chave_publica_comprimida)
        ripemd160_bpk = hashlib.new("ripemd160")
        ripemd160_bpk.update(sha256_bpk.digest())
        hashed_public_key = ripemd160_bpk.digest()
        endereco_legacy = base58.b58encode_check(b"\x00" + hashed_public_key).decode('utf-8')
        witness_version = 0
        witness_program = bech32.convertbits(hashed_public_key, 8, 5)
        endereco_segwit = bech32.bech32_encode('bc', [witness_version] + witness_program)
        wif_versioned_key = b"\x80" + chave_privada_bytes
        wif_versioned_key_compressed = wif_versioned_key + b"\x01"
        chave_wif = base58.b58encode_check(wif_versioned_key_compressed).decode('utf-8')

        print(f"\n{Fore.CYAN}--- RESULTADO ---")
        print(f"{Style.BRIGHT}Número Decimal:{Style.NORMAL} {numero}")
        print(f"{Style.BRIGHT}Chave Privada (Hex):{Style.NORMAL} {chave_privada_hex}")
        print(f"{Style.BRIGHT}Chave Privada (WIF):{Style.NORMAL} {chave_wif}")
        print(f"{Style.BRIGHT}Endereço Legacy (P2PKH):{Style.NORMAL} {endereco_legacy}")
        print(f"{Style.BRIGHT}Endereço SegWit (Bech32):{Style.NORMAL} {endereco_segwit}")
        print(f"\n{Fore.CYAN}--- VERIFICANDO SALDOS ONLINE ---")
        verificar_saldo(endereco_legacy, "Legacy")
        verificar_saldo(endereco_segwit, "SegWit")
        print(f"{Fore.CYAN}---------------------------------")
    except Exception as e:
        print(f"\n{Fore.RED}Erro ao gerar a chave para o número {numero}: {e}")

def converter_chave():
    """Converte uma chave WIF/Hex e mostra seus detalhes."""
    chave_input = input("Digite a chave privada (em formato WIF ou Hexadecimal): ").strip()
    try:
        chave_privada_bytes = None
        if chave_input.startswith(('K', 'L', '5')):
            chave_decodificada = base58.b58decode_check(chave_input)
            chave_privada_bytes = chave_decodificada[1:33]
        else:
            if len(chave_input) > 64:
                print(f"{Fore.RED}Erro: Uma chave hexadecimal não pode ter mais de 64 caracteres.")
                return
            chave_hex_completa = chave_input.zfill(64)
            chave_privada_bytes = bytes.fromhex(chave_hex_completa)
        numero_decimal = int.from_bytes(chave_privada_bytes, 'big')
        print("\nConvertendo chave...")
        gerar_chave(numero_decimal)
    except Exception as e:
        print(f"\n{Fore.RED}Erro ao decodificar ou processar a chave: {e}")

def calculadora_range_inteligente():
    """Calcula um ponto de partida em um range (porcentagem ou aleatório)."""
    try:
        range_input = input("Digite o range (INICIO:FIM) em hexadecimal: ").strip().lower()
        partes = range_input.split(':')
        if len(partes) != 2:
            print(f"\n{Fore.RED}Erro: Formato inválido. Use INICIO:FIM.")
            return
        range_inicio_hex, range_fim_hex = partes[0], partes[1]
        inicio_decimal = int(range_inicio_hex, 16)
        fim_decimal = int(range_fim_hex, 16)
        if inicio_decimal >= fim_decimal:
            print(f"\n{Fore.RED}Erro: O range inicial deve ser menor que o range final.")
            return
        escolha = input("Deseja definir uma porcentagem específica? (s/n): ").strip().lower()
        novo_inicio_decimal = 0
        info_calculo = ""
        if escolha == 's':
            porcentagem_str = input("Digite a porcentagem (ex: 50.123): ").strip().replace(',', '.')
            porcentagem = float(porcentagem_str)
            if not (0 <= porcentagem <= 100):
                print(f"\n{Fore.RED}Erro: A porcentagem deve estar entre 0 e 100.")
                return
            tamanho_total_range = fim_decimal - inicio_decimal
            offset = int(tamanho_total_range * (porcentagem / 100.0))
            novo_inicio_decimal = inicio_decimal + offset
            info_calculo = f"Cálculo para: {porcentagem}%"
        elif escolha == 'n':
            novo_inicio_decimal = random.randint(inicio_decimal, fim_decimal)
            tamanho_total_range = fim_decimal - inicio_decimal
            if tamanho_total_range > 0:
                offset = novo_inicio_decimal - inicio_decimal
                porcentagem_aleatoria = (offset / tamanho_total_range) * 100
                info_calculo = f"Sugestão Aleatória (correspondente a {porcentagem_aleatoria:.4f}% do range):"
            else:
                info_calculo = "Sugestão Aleatória:"
        else:
            print(f"\n{Fore.RED}Opção inválida. Responda com 's' ou 'n'.")
            return
        novo_inicio_hex = hex(novo_inicio_decimal)[2:]
        range_final = f"{novo_inicio_hex}:{range_fim_hex}"
        print(f"\n{Fore.CYAN}------------------------------------")
        print(f"{Style.BRIGHT}{info_calculo}")
        print(f"\n{Style.NORMAL}Range para Keyhunt (copie e cole):")
        print(f"{Style.BRIGHT}{range_final}")
        print(f"{Fore.CYAN}------------------------------------")
        
        # Chama a nova função auxiliar
        gerar_comando_keyhunt_opcional(range_final)

    except ValueError:
        print(f"\n{Fore.RED}Erro: Entrada inválida. Verifique os hexadecimais.")
    except Exception as e:
        print(f"\n{Fore.RED}Ocorreu um erro inesperado: {e}")

def definir_zona_de_busca():
    """Define uma 'janela de busca' precisa com base em um ponto de partida e um tamanho."""
    try:
        print(f"\n{Fore.CYAN}### Definir Zona de Busca Precisa ###")
        range_input = input("Digite o range TOTAL (INICIO:FIM) em hexadecimal: ").strip().lower()
        partes = range_input.split(':')
        if len(partes) != 2:
            print(f"\n{Fore.RED}Erro: Formato inválido. Use INICIO:FIM.")
            return
        base_inicio_hex, base_fim_hex = partes[0], partes[1]
        base_inicio_dec = int(base_inicio_hex, 16)
        base_fim_dec = int(base_fim_hex, 16)
        if base_inicio_dec >= base_fim_dec:
            print(f"\n{Fore.RED}Erro: O range inicial deve ser menor que o range final.")
            return
        range_total_dec = base_fim_dec - base_inicio_dec

        start_percent_str = input(f"{Style.BRIGHT}Passo 1:{Style.NORMAL} Em qual % do range total você quer COMEÇAR a busca? ").strip().replace(',', '.')
        start_percent = float(start_percent_str)
        if not (0 <= start_percent < 100): # Início não pode ser 100%
            print(f"\n{Fore.RED}Erro: A porcentagem de início deve estar entre 0 e 99.99...%.")
            return

        size_percent_str = input(f"{Style.BRIGHT}Passo 2:{Style.NORMAL} Qual o TAMANHO da sua janela de busca (como % do range total)? ").strip().replace(',', '.')
        size_percent = float(size_percent_str)
        if not (0 < size_percent <= 100):
            print(f"\n{Fore.RED}Erro: A porcentagem de tamanho deve ser maior que 0 e no máximo 100.")
            return

        offset_inicio = int(range_total_dec * (start_percent / 100.0))
        novo_inicio_dec = base_inicio_dec + offset_inicio
        tamanho_janela_dec = int(range_total_dec * (size_percent / 100.0))
        novo_fim_dec = novo_inicio_dec + tamanho_janela_dec
        novo_fim_dec = min(novo_fim_dec, base_fim_dec)
        novo_inicio_hex = hex(novo_inicio_dec)[2:]
        novo_fim_hex = hex(novo_fim_dec)[2:]
        range_final = f"{novo_inicio_hex}:{novo_fim_hex}"

        print(f"\n{Fore.CYAN}---------------------------------------------------------")
        print(f"{Style.BRIGHT}Zona de Busca Definida:")
        print(f"{Style.NORMAL}(Iniciando em {start_percent}%, com um tamanho de {size_percent}% do range total)")
        print(f"\n{Style.NORMAL}Copie este range para sua ferramenta de busca randômica:")
        print(f"{Style.BRIGHT}{range_final}")
        print(f"{Fore.CYAN}---------------------------------------------------------")
        
        # Chama a nova função auxiliar
        gerar_comando_keyhunt_opcional(range_final)

    except ValueError:
        print(f"\n{Fore.RED}Erro: Entrada inválida. Verifique os hexadecimais e as porcentagens.")
    except Exception as e:
        print(f"\n{Fore.RED}Ocorreu um erro inesperado: {e}")

# --- PROGRAMA PRINCIPAL ---
def main():
    """Função principal que executa o menu em loop."""
    init(autoreset=True) # Inicia o colorama para que as cores funcionem e se resetem
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}### Ferramenta de Chaves Bitcoin ###")
        print(f"{Fore.YELLOW}1: Gerar chave por número (+saldo)")
        print(f"{Fore.YELLOW}2: Gerar chaves em intervalo (+saldos)")
        print(f"{Fore.YELLOW}3: Converter chave (+saldo)")
        print(f"{Fore.YELLOW}4: Calculadora de Range Inteligente")
        print(f"{Fore.YELLOW}5: Definir Zona de Busca Precisa")
        print(f"{Fore.YELLOW}6: Sair")
        
        escolha = input(f"{Style.BRIGHT}Escolha uma opção: {Style.NORMAL}")

        if escolha == '1':
            try:
                numero = int(input("Digite o número decimal para gerar a chave: "))
                gerar_chave(numero)
            except ValueError:
                print(f"{Fore.RED}Entrada inválida. Por favor, digite um número.")
        
        elif escolha == '2':
            try:
                inicio = int(input("Digite o número INICIAL do range (decimal): "))
                fim = int(input("Digite o número FINAL do range (decimal): "))
                if inicio >= fim:
                    print(f"{Fore.RED}O número inicial deve ser menor que o final.")
                else:
                    print(f"\nGerando chaves de {inicio} até {fim}...")
                    for numero in range(inicio, fim + 1):
                        gerar_chave(numero)
            except ValueError:
                print(f"{Fore.RED}Entrada inválida. Por favor, digite números.")
                
        elif escolha == '3':
            converter_chave()
            
        elif escolha == '4':
            calculadora_range_inteligente()
            
        elif escolha == '5':
            definir_zona_de_busca()

        elif escolha == '6':
            print("Saindo do programa.")
            break
            
        else:
            print(f"{Fore.RED}Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()

