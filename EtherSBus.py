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
from time import sleep


class Configurator:  # Класс, который позволяет задать параметры для полей единым образом
    def __init__(self, C_type, C_IP, register, flag):  # register - R****, flag - F***
        if C_type == "Temperature":
            self.C_type = 0
        elif C_type == "Pressure":
            self.C_type = 1
        elif C_type == "Humidity":
            self.C_type = 2
        self.C_IP = C_IP
        self.reg = register
        self.flag = flag


def change_value(position, parameter):  # Функция изменение значения в поле
    if position == 0:
        Nexser.write(('t'+str(6)+'.txt="'+str(parameter)+' °C"').encode())
        Nexser.write(end)  # end - структура b'xff' или же char(255)
    elif position == 1:
        Nexser.write(('t' + str(7)+'.txt="'+str(parameter)+' Pa"').encode())
        Nexser.write(end)  # end - структура b'xff' или же char(255)
    elif position == 2:
        Nexser.write(('t' + str(8)+'.txt="'+str(parameter)+' %"').encode())
        Nexser.write(end)  # end - структура b'xff' или же char(255)


def change_color(position, status):  # Функция изменения цвета поля
    if status == 0:  # Если в регистре хранится 0 - цвет экрана зелёный2
        for a in range(3, 9, 3):
            Nexser.write(('t'+str(position + a)+'.bco='+str(2016)).encode())
            Nexser.write(end)  # k - структура b'xff' или же char(255)

    else:
        for a in range(3, 9, 3):
            Nexser.write(('t' + str(position + a) + '.bco=' + str(63488)).encode())
            Nexser.write(end)  # k - структура b'xff' или же char(255)

"""def name_room(room):
    
    Nexser.write(('t' + str(6) + '.txt="' + str(room) + ' °C"').encode())
    Nexser.write(end)  # end - структура b'xff' или же char(255)
"""
# Задаём параметры опрашиваемых полей: значение; IP PLC, к которому мы обращаемся; регистр и флаг для параметра

temperature = Configurator("Temperature", "192.168.99.3", register=2008, flag=2008)
pressure = Configurator("Pressure", "192.168.99.3", register=2009, flag=2009)
humidity = Configurator("Humidity", "192.168.99.1", register=22, flag=2008)
#name = "Room 1-946 Vesta C"
end = struct.pack('3B', 0xff, 0xff, 0xff)  # Окончание посылок в Serial
Nexser = serial.Serial(
    port='/dev/ttyS1',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0.2,  # timeout in reception in seconds
)
node = SAIANode(lid=0)  # Создаём объект node

# Запускаем первый сервер, обозначаем значения только для чтения, связываемся с флагом и регистром
server1 = node.servers.declare(temperature.C_IP)
server1.setReadOnly()
server1.memory.flags.declare(index=temperature.flag)
server1.memory.registers.declare(index=temperature.reg)
# Запускаем второй сервер, если IP одинаковый, то новый сервер создаваться не будет
server2 = node.servers.declare(pressure.C_IP)
server2.setReadOnly()
server2.memory.flags.declare(index=pressure.flag)
server2.memory.registers.declare(index=pressure.reg)
# Запускаем третий сервер
server3 = node.servers.declare(humidity.C_IP)
server3.setReadOnly()
server3.memory.flags.declare(index=humidity.flag)
server3.memory.registers.declare(index=humidity.reg)

node.refresh()  # Сделать запрос в Сеть и обновить значения всех регистров и флагов для всех серверов
sleep(1)  # Сон, чтобы дать время фоновой задаче обработать ответ от серверов

# Первичное отображение значений на экране
"""name_room(name)"""
change_color(temperature.C_type, server1.flags[temperature.flag].value)
change_value(temperature.C_type, server1.registers[temperature.reg].int10)
change_color(pressure.C_type, server2.flags[pressure.flag].value)
change_value(pressure.C_type, server2.registers[pressure.reg].int10)
change_color(humidity.C_type, server3.flags[humidity.flag].value)
change_value(humidity.C_type, server3.registers[humidity.reg].int10)

while node.isRunning():  # Пока всё работает нормально (нет прерываний, ошибок)
    try:
        while True:
            if server1.flags[temperature.flag].age() > 0.5:  # Если прошло больше 4-х секунд с предыдущего опроса
                node.refresh()  # Запрос в Сеть на обновление значений всех регистров и флагов для всех серверов
                sleep(0.5)  # Сон, чтобы дать время фоновой задаче обработать ответ от серверов
                # Если изменился флаг температуры
                change_color(temperature.C_type, server1.flags[temperature.flag].value)
                # Если изменился флаг давления
                change_color(pressure.C_type, server2.memory.flags[pressure.flag].value)
                # Если изменился флаг влажности
                change_color(humidity.C_type, server3.memory.flags[humidity.flag].value)
                # Если изменилось значение температуры
                change_value(temperature.C_type, server1.memory.registers[temperature.reg].int10)
                # Если изменилось значение давления
                change_value(pressure.C_type, server2.memory.registers[pressure.reg].int10)
                # Если изменилось значение влажности
                change_value(humidity.C_type, server3.memory.registers[humidity.reg].int10)
            #else:
            #    sleep(1)

    except:
        node.close()
        break

"""from digimat.saia import SAIANode
import serial
import struct
from time import sleep
from time import time

class Configurator:
    def __init__(self, C_type, C_IP, register, flag):
        if C_type == "Temperature":
            self.C_type = 0
        elif C_type == "Pressure":
            self.C_type = 1
        elif C_type == "Humidity":
            self.C_type = 2
        self.C_IP = C_IP
        self.reg = register
        self.flag = flag


def change_value(position, parameter):
    if position == 0:
        Nexser.write(('t'+str(6)+'.txt="'+str(parameter)+' °C"').encode())
        Nexser.write(end)  # end - структура b'xff' или же char(255)
    elif position == 1:
        Nexser.write(('t' + str(7)+'.txt="'+str(parameter)+' Pa"').encode())
        Nexser.write(end)  # end - структура b'xff' или же char(255)
    elif position == 2:
        Nexser.write(('t' + str(8)+'.txt="'+str(parameter)+' %"').encode())
        Nexser.write(end)  # end - структура b'xff' или же char(255)


def change_color(position, status):
    if status == 0:
        for a in range(0, 9, 3):
            Nexser.write(('t'+str(position + a)+'.bco='+str(2016)).encode())
            Nexser.write(end)  # k - структура b'xff' или же char(255)

    else:
        for a in range(0, 9, 3):
            Nexser.write(('t' + str(position + a) + '.bco=' + str(63488)).encode())
            Nexser.write(end)  # k - структура b'xff' или же char(255)


start = time()

temperature = Configurator("Temperature", "192.168.99.1", register=22, flag=22)
pressure = Configurator("Pressure", "192.168.99.1", register=23, flag=23)
humidity = Configurator("Humidity", "192.168.99.1", register=24, flag=24)
list_items = [temperature, pressure, humidity]

end = struct.pack('3B', 0xff, 0xff, 0xff)
Nexser = serial.Serial(
    port='/dev/ttyS1',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0.2,  # timeout in reception in seconds
)
node = SAIANode(lid=0)
# Starting servers
#(node.servers[temperature.C_IP]).registers.declare
server1 = node.servers.declare(temperature.C_IP)
server1.setReadOnly()
server1.memory.flags.declare(index=temperature.flag)
server1.memory.registers.declare(index=temperature.reg)


server2 = node.servers.declare(pressure.C_IP)
server2.setReadOnly()
server2.memory.flags.declare(index=pressure.flag)
server2.memory.registers.declare(index=pressure.reg)



server3 = node.servers.declare(humidity.C_IP)
server3.setReadOnly()
server3.memory.flags.declare(index=humidity.flag)
server3.memory.registers.declare(index=humidity.reg)

node.refresh()
sleep(1)

old_values = [server1.flags[temperature.flag].value, server2.flags[pressure.flag].value,
              server3.flags[humidity.flag].value, server1.registers[temperature.reg].int10,
              server2.registers[pressure.reg].int10, server3.registers[humidity.reg].int10]

print(old_values)

change_color(temperature.C_type, old_values[0])
change_value(temperature.C_type, old_values[3])
change_color(pressure.C_type, old_values[1])
change_value(pressure.C_type, old_values[4])
change_color(humidity.C_type, old_values[2])
change_value(humidity.C_type, old_values[5])

print(time()-start)

while node.isRunning():
    try:
        while True:
            if server1.flags[temperature.flag].age() > 4:
                node.refresh()
                sleep(1)
                start = time()
                if old_values[0] != server1.flags[temperature.flag].value:
                    old_values[0] = server1.flags[temperature.flag].value
                    change_color(temperature.C_type, old_values[0])
                if old_values[1] != server2.memory.flags[pressure.flag].value:
                    old_values[1] = server2.memory.flags[pressure.flag].value
                    change_color(pressure.C_type, old_values[1])
                if old_values[2] != server3.memory.flags[humidity.flag].value:
                    old_values[2] = server3.memory.flags[humidity.flag].value
                    change_color(humidity.C_type, old_values[2])
                if old_values[3] != server1.memory.registers[temperature.reg].int10:
                    old_values[3] = server1.memory.registers[temperature.reg].int10
                    change_value(temperature.C_type, old_values[3])
                if old_values[4] != server2.memory.registers[pressure.reg].int10:
                    old_values[4] = server2.memory.registers[pressure.reg].int10
                    change_value(pressure.C_type, old_values[4])
                if old_values[5] != server3.memory.registers[humidity.reg].int10:
                    old_values[5] = server3.memory.registers[humidity.reg].int10
                    change_value(humidity.C_type, old_values[5])
                print(time() - start)
            else:
                pass



    except:
        node.close()
        break
"""
"""
from digimat.saia import SAIANode
import serial
import struct
from time import sleep

class Configurator:
    def __init__(self, C_type, C_IP, register, flag):
        if C_type == "Temperature":
            self.C_type = 0
        elif C_type == "Pressure":
            self.C_type = 1
        elif C_type == "Humidity":
            self.C_type = 2
        self.C_IP = C_IP
        self.reg = register
        self.flag = flag

def change_value(position, parameter):
    print(position, parameter)
    if position == 0:
        Nexser.write(('t'+str(6)+'.txt="'+str(parameter)+' °C"').encode())
        Nexser.write(end)  # end - структура b'xff' или же char(255)
    elif position == 1:
        Nexser.write(('t' + str(7)+'.txt="'+str(parameter)+' Pa"').encode())
        Nexser.write(end)  # end - структура b'xff' или же char(255)
    elif position == 2:
        Nexser.write(('t' + str(8)+'.txt="'+str(parameter)+' %"').encode())
        Nexser.write(end)  # end - структура b'xff' или же char(255)


def change_color(position, status):
    print(position, status)
    if status == 0:
        for a in range(0, 9, 3):
            Nexser.write(('t'+str(position + a)+'.bco='+str(2016)).encode())
            Nexser.write(end)  # k - структура b'xff' или же char(255)
    else:
        for a in range(0, 9, 3):
            Nexser.write(('t' + str(position + a) + '.bco=' + str(63488)).encod>
            Nexser.write(end)  # k - структура b'xff' или же char(255)


temperature = Configurator("Temperature", "169.254.8.132", register=1010, flag=>
pressure = Configurator("Pressure", "169.254.8.132", register=1011, flag=11)
humidity = Configurator("Humidity", "169.254.8.132", 2008, 2009)
end = struct.pack('3B', 0xff, 0xff, 0xff)
Nexser = serial.Serial(
    port='/dev/ttyS1',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0.2,  # timeout in reception in seconds
)

node = SAIANode(lid=0)
# Starting servers
server1 = node.servers.declare(temperature.C_IP)
server1.setReadOnly()
server1.memory.flags.declare(index=temperature.flag)
server1.memory.registers.declare(index=temperature.reg)
server1.refresh()
#(node.servers[temperature.C_IP]).registers.declare

server2 = node.servers.declare(pressure.C_IP)
server2.setReadOnly()
server2.memory.flags.declare(index=pressure.flag)
server2.memory.registers.declare(index=pressure.reg)
server2.refresh()


server3 = node.servers.declare(humidity.C_IP)
server3.setReadOnly()
server3.memory.flags.declare(index=humidity.flag)
server3.memory.registers.declare(index=humidity.reg)

server3.refresh()

sleep(1)

old_values = [server1.flags[temperature.flag].value, server2.flags[pressure.fla>
              server3.flags[humidity.flag].value, server1.registers[temperature>
              server2.registers[pressure.reg].int10, server3.registers[humidity>

print(old_values)

change_color(temperature.C_type, server1.memory.flags[temperature.flag].value)
change_value(temperature.C_type, server1.memory.registers[temperature.reg].int1>
change_color(pressure.C_type, server2.memory.flags[pressure.flag].value)
change_value(pressure.C_type, server2.memory.registers[pressure.reg].int10)
change_color(humidity.C_type, server3.memory.flags[humidity.flag].value)
change_value(humidity.C_type, server3.memory.registers[humidity.reg].int10)

while node.isRunning():
    try:
        while True:

            if server1.flags[temperature.flag].age() > 4:
                print(server1.flags[temperature.flag].age())
                node.refresh()
                sleep(1)
                change_color(temperature.C_type, server1.memory.flags[temperatu>
                change_value(temperature.C_type, server1.memory.registers[tempe>
                change_color(pressure.C_type, server2.memory.flags[pressure.fla>
                change_value(pressure.C_type, server2.memory.registers[pressure>
                change_color(humidity.C_type, server3.memory.flags[humidity.fla>
                change_value(humidity.C_type, server3.memory.registers[humidity>
                node.table()
            else:
                pass



    except:
        node.close()
        break

"""