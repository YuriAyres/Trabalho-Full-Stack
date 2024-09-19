import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from time import sleep, time
import signal
import sys
import csv
from autorizacao import Autorizacoes
from negacao import Negacoes

# Configurações de hardware
GPIO.setmode(GPIO.BOARD)
LED_VERDE = 8
LED_VERMELHO = 10
BUZZER = 12

GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_VERMELHO, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

# Iniciando o leitor RFID
leitorRfid = SimpleMFRC522()

# Controle de acessos
acessos_hoje = {}
tempo_entrada = {}
tentativas_negadas = {}
tentativas_invasao = 0

# Instâncias de Autorizacoes e Negacoes
autorizacoes = Autorizacoes()
negacoes = Negacoes()

# Funções para o buzzer
def tocar_buzzer(frequencia, duracao):
    p = GPIO.PWM(BUZZER, frequencia)
    p.start(50)  # Duty cycle de 50%
    sleep(duracao)
    p.stop()

def buzzer_entrada_autorizada():
    tocar_buzzer(1000, 0.2)  # Som curto de entrada autorizada

def buzzer_acesso_negado():
    tocar_buzzer(500, 0.5)  # Som de alerta médio

def buzzer_tentativa_invasao():
    tocar_buzzer(300, 1.0)  # Som de alerta longo

# Função para salvar relatório CSV
def salvar_relatorio_csv():
    with open('relatorio_acessos.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Colaborador", "Tempo Total (horas)", "Tentativas de Acesso Negadas", "Tentativas de Invasão"])
        
        # Relatório para usuários autorizados (com acessos)
        for tag, tempos in tempo_entrada.items():
            nome = autorizacoes.get(tag, "Desconhecido")
            tempo_total = sum([saida - entrada for entrada, saida in tempos if saida is not None]) / 3600  # Em horas
            writer.writerow([nome, f"{tempo_total:.2f}", tentativas_negadas.get(nome, 0), tentativas_invasao])

        # Relatório de tentativas negadas
        for tag, nome in negacoes.items():
            if tag not in tempo_entrada:  # Usuários que nunca conseguiram entrar
                writer.writerow([nome, "0.00", tentativas_negadas.get(nome, 0), tentativas_invasao])

        # Relatório de tentativas de invasão (tags não reconhecidas)
        writer.writerow(["Invasão Desconhecida", "N/A", "N/A", tentativas_invasao])


# Função para finalizar o programa
def finalizar_programa(signal, frame):
    print("\nRelatório de acessos e tentativas:")
    
    for tag, tempos in tempo_entrada.items():
        nome = autorizacoes[tag]
        tempo_total = sum([saida - entrada for entrada, saida in tempos if saida is not None])
        print(f"Colaborador {nome} ficou {tempo_total / 3600:.2f} horas na sala.")
    
    print("\nTentativas de acesso negadas:")
    for nome, tentativas in tentativas_negadas.items():
        print(f"{nome} tentou acessar {tentativas} vez(es).")
    
    print(f"\nTotal de tentativas de invasão: {tentativas_invasao}")

    # Salvar relatório no CSV
    salvar_relatorio_csv()

    GPIO.cleanup()
    sys.exit(0)

# Captura o sinal de interrupção (CTRL+C)
signal.signal(signal.SIGINT, finalizar_programa)

try:
    while True:
        print("Aguardando leitura da tag...")
        tag, nome = leitorRfid.read()
        print(f"ID do cartão: {tag}")
        
        if tag in autorizacoes:
            nome = autorizacoes[tag]
            
            if tag not in acessos_hoje:
                # Primeira entrada do colaborador
                acessos_hoje[tag] = True
                tempo_entrada[tag] = tempo_entrada.get(tag, []) + [(time(), None)]
                print(f"Acesso autorizado, Bem-vindo(a) {nome}!")
                
                GPIO.output(LED_VERDE, GPIO.HIGH)
                buzzer_entrada_autorizada()
                sleep(5)
                GPIO.output(LED_VERDE, GPIO.LOW)
            else:
                # Verifica se a última entrada ainda não teve saída
                if tempo_entrada[tag][-1][1] is None:
                    # Marca a saída
                    tempo_entrada[tag][-1] = (tempo_entrada[tag][-1][0], time())
                    print(f"Saída autorizada, até logo {nome}!")
                else:
                    # Registra uma nova entrada
                    tempo_entrada[tag].append((time(), None))
                    print(f"Acesso autorizado, Bem-vindo(a) de volta {nome}!")
                
                GPIO.output(LED_VERDE, GPIO.HIGH)
                buzzer_entrada_autorizada()
                sleep(5)
                GPIO.output(LED_VERDE, GPIO.LOW)
        
        elif tag in negacoes:
            nome = negacoes[tag]
            print(f"Acesso negado, você não tem acesso a este projeto {nome}.")
            tentativas_negadas[nome] = tentativas_negadas.get(nome, 0) + 1
            GPIO.output(LED_VERMELHO, GPIO.HIGH)
            buzzer_acesso_negado()
            sleep(5)
            GPIO.output(LED_VERMELHO, GPIO.LOW)
        
        else:
            print("Identificação não encontrada!")
            tentativas_invasao += 1
            buzzer_tentativa_invasao()
            for _ in range(10):
                GPIO.output(LED_VERMELHO, GPIO.HIGH)
                sleep(0.5)
                GPIO.output(LED_VERMELHO, GPIO.LOW)
                sleep(0.5)

finally:
    GPIO.cleanup()
