#!/usr/bin/env python
# -*- coding^ utf-8 -*-
#  Эта программа имитирует работу для экрана Room 1-928, Ra_928_D1 (Solopharm 19)
#  Экран выступает в качестве мастера и опрашивает PLC с определённой частотой
#  Её наверное не стоит делать слишком большой, иначе канал передачи будет занят всё время
#  IP Address 192.168.99.58, но мы пока используем 169.254.8.131 т.к. Ethernet адаптер
#  PLC_1 IP Address 192.168.99.1, S-Bus Address 0, параметр обновление активного списка - 4 сек
#  Частота обновления тегов, группы (экрана) 500 мс.


from digimat.saia import SAIANode
import serial
import struct


class Configurator:  # Класс, который позволяет задать параметры для полей един>
    def __init__(self, C_type, C_IP, status, register, flag):  # register - R****, flag>
        if C_type == "Temperature":
            self.C_type = 0
        elif C_type == "Pressure":
            self.C_type = 1
        elif C_type == "Humidity":
            self.C_type = 2
        self.status = status
        self.C_IP = C_IP
        self.reg = register
        self.flag = flag


def change_value(position, parameter):  # Функция изменение значения в поле
    if parameter != "*":
        if position == 0:
            Nexser.write(('t' + str(6) + '.txt="' + str(parameter) + ' °C"').encode())
        elif position == 1:
            Nexser.write(('t' + str(7) + '.txt="' + str(parameter) + ' Pa"').encode())
        elif position == 2:
            Nexser.write(('t' + str(8) + '.txt="' + str(parameter) + ' %"').encode())
    else:
        Nexser.write(('t' + str(6 + position) + '.txt="' + str(parameter * 5) + '"').encode())
    Nexser.write(end)  # end - структура b'xff' или же char(255)


def change_color(position, status):  # Функция изменения цвета поля
    if status == 0:  # Если в регистре хранится 0 - цвет экрана зелёный2
        for a in range(3, 9, 3):
            Nexser.write(('t' + str(position + a) + '.bco=' + str(2016)).encode())
            Nexser.write(end)  # k - структура b'xff' или же char(255)

    else:
        for a in range(3, 9, 3):
            Nexser.write(('t' + str(position + a) + '.bco=' + str(63488)).encode())
            Nexser.write(end)  # k - структура b'xff' или же char(255)


end = struct.pack('3B', 0xff, 0xff, 0xff)  # Окончание посылок в Serial

Nexser = serial.Serial(
    port='/dev/ttyS1',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0.2,  # timeout in reception in seconds
    )

# Задаём параметры опрашиваемых полей: значение; IP PLC, к которому мы обращаемся; регистр и флаг для параметра
temperature = Configurator('Temperature', '192.168.0.14', 'ON', register=22, flag=22)
pressure = Configurator('Pressure', '192.168.0.12', 'ON', register=23, flag=23)
humidity = Configurator('Humidity', '192.168.0.11', 'OFF', register=22, flag=22)
try:
    TPH = [temperature, pressure, humidity]
except NameError:
    TPH = [temperature, pressure]

# name = "Room 1-946 Vesta C"

node = SAIANode(lid=253)  # Создаём объект node

servers = []

for i, parameter in enumerate(TPH):
    servers.append(node.servers.declare(parameter.C_IP))
    servers[i].setReadOnly()
    servers[i].memory.flags.declare(index=parameter.flag)
    servers[i].memory.registers.declare(index=parameter.reg)
node.sleep(1)

while node.isRunning():  # Пока всё работает нормально (нет прерываний, ошибок)
    try:
        for server, parameter in zip(servers, TPH):
            if not server.isAlive():
                server.setReadOnly()
                server.memory.flags.declare(index=parameter.flag)
                server.memory.registers.declare(index=parameter.reg)
            if server.status != 82:
                change_color(parameter.C_type, 1)
                change_value(parameter.C_type, "*")
            else:
                change_color(parameter.C_type, server.flags[parameter.flag].value)
                change_value(parameter.C_type, server.memory.registers[parameter.reg].int10)
        node.refresh()  # Запрос в Сеть на обновление значений всех регистров и флагов для всех серверов
        node.sleep(0.5)
    except:
        node.close()
        break
