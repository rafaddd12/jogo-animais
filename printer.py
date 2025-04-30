from escpos.printer import BluetoothPrinter
import time

class ThermalPrinter:
    def __init__(self):
        self.printer = None
        self.device_address = None

    def connect(self, device_address):
        """Conecta à impressora Bluetooth"""
        try:
            self.printer = BluetoothPrinter(device_address)
            self.device_address = device_address
            return True
        except Exception as e:
            print(f"Erro ao conectar à impressora: {str(e)}")
            return False

    def print_result(self, aposta, resultado, chance_real):
        """Imprime o resultado da aposta"""
        if not self.printer:
            return False

        try:
            # Cabeçalho
            self.printer.set(align='center')
            self.printer.text("JOGO DE ANIMAIS\n")
            self.printer.text("================\n\n")

            # Dados da aposta
            self.printer.set(align='left')
            self.printer.text(f"Valor: R$ {aposta:.2f}\n")
            self.printer.text(f"Chance: {chance_real:.2f}%\n")
            self.printer.text(f"Resultado: {resultado}\n")

            # Rodapé
            self.printer.set(align='center')
            self.printer.text("\n================\n")
            self.printer.text(f"Data: {time.strftime('%d/%m/%Y %H:%M:%S')}\n")
            
            # Corta o papel
            self.printer.cut()
            return True
        except Exception as e:
            print(f"Erro ao imprimir: {str(e)}")
            return False

    def disconnect(self):
        """Desconecta da impressora"""
        if self.printer:
            self.printer.close()
            self.printer = None
            self.device_address = None 