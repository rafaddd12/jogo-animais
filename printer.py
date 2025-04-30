try:
    from escpos.printer import BluetoothPrinter
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
import time

class ThermalPrinter:
    def __init__(self):
        self.printer = None
        self.device_address = None
        self.is_mock = not BLUETOOTH_AVAILABLE
        if self.is_mock:
            print("Aviso: Usando versão simulada da impressora (sem Bluetooth)")

    def connect(self, device_address):
        """Conecta à impressora Bluetooth ou usa modo simulado"""
        try:
            if not self.is_mock:
                self.printer = BluetoothPrinter(device_address)
                self.device_address = device_address
                print("Impressora Bluetooth conectada com sucesso")
            else:
                print("Modo simulado: Impressora conectada (simulação)")
            return True
        except Exception as e:
            print(f"Erro ao conectar à impressora: {str(e)}")
            self.is_mock = True
            print("Alternando para modo simulado")
            return True

    def print_result(self, aposta, resultado, chance_real):
        """Imprime ou simula a impressão do resultado da aposta"""
        try:
            if not self.is_mock and self.printer:
                # Impressão real via Bluetooth
                self.printer.set(align='center')
                self.printer.text("JOGO DE ANIMAIS\n")
                self.printer.text("================\n\n")
                self.printer.set(align='left')
                self.printer.text(f"Valor: R$ {aposta:.2f}\n")
                self.printer.text(f"Chance: {chance_real:.2f}%\n")
                self.printer.text(f"Resultado: {resultado}\n")
                self.printer.set(align='center')
                self.printer.text("\n================\n")
                self.printer.text(f"Data: {time.strftime('%d/%m/%Y %H:%M:%S')}\n")
                self.printer.cut()
            else:
                # Modo simulado - apenas imprime no console
                print("\n=== SIMULAÇÃO DE IMPRESSÃO ===")
                print("JOGO DE ANIMAIS")
                print("================")
                print(f"Valor: R$ {aposta:.2f}")
                print(f"Chance: {chance_real:.2f}%")
                print(f"Resultado: {resultado}")
                print("================")
                print(f"Data: {time.strftime('%d/%m/%Y %H:%M:%S')}")
                print("===========================\n")
            return True
        except Exception as e:
            print(f"Erro ao imprimir: {str(e)}")
            return False

    def disconnect(self):
        """Desconecta da impressora ou finaliza simulação"""
        if not self.is_mock and self.printer:
            self.printer.close()
        self.printer = None
        self.device_address = None
        print("Impressora desconectada" if not self.is_mock else "Simulação finalizada") 