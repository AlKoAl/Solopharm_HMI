#!/usr/bin/env python
# -*- coding^ utf-8 -*-
#  Эта программа имеет возможность опрашивать до 3-х PCD с одинаковыми или различными ID
#  Изменён файл /usr/local/lib/python3.10/dist-packages/digimat/saia/server.py (смотри github.com/AlKoAl/digimat-saia)
#  Локальный ID (lid) всегда установлен в 253. Параметры сети платы задаются отдельно с помощь файла init_setings.sh
#  Там же содержатся инструкции по перезаписи этого файла (адресов опрашиваемых контроллеров и регистры)
#  Скорость опроса PCD - раз в 0.5 с.


from digimat.saia import SAIANode
import serial
import struct


class Configurator:  # Класс, который позволяет задать параметры для полей един>
    def __init__(self, C_type, C_IP, status, register, flag):
        if C_type == "Temperature":
            self.C_type = 0
        elif C_type == "Pressure":
            self.C_type = 1
        elif C_type == "Humidity":
            self.C_type = 2
        self.status = status  # Нужно ли нам поле или нет, будет ли оно опрашиваться
        self.C_IP = C_IP  # IP адрес, откуда берутся параметры
        self.reg = register  # регистр ПЛК, откуда берётся значение
        self.flag = flag  # флаг ПЛК, откуда берётся цвет поля (красный или зелёный)


def change_value(position, parameter):  # Функция изменение значения в поле
    if parameter != "*":  # Если нам передали число, то выводим его
        if position == 0:
            Nexser.write(('t' + str(6) + '.txt="' + str(parameter) + ' °C"').encode())
        elif position == 1:
            Nexser.write(('t' + str(7) + '.txt="' + str(parameter) + ' Pa"').encode())
        elif position == 2:
            Nexser.write(('t' + str(8) + '.txt="' + str(parameter) + ' %"').encode())
    else:  # Если передали звёздочку, заполняем ею поле, значит есть ошибка
        Nexser.write(('t' + str(6 + position) + '.txt="' + str(parameter * 5) + '"').encode())
    Nexser.write(end)  # end - структура b'xff' или же char(255)


def change_color(position, status):  # Функция изменения цвета поля
    if status == 0:  # Если во флаге хранится 0 - цвет экрана зелёный 2016
        for a in range(3, 9, 3):
            Nexser.write(('t' + str(position + a) + '.bco=' + str(2016)).encode())
            Nexser.write(end)  # k - структура b'xff' или же char(255)
    else:  # Если во флаге лежит значение 1, то меняем цвет на красный 63488
        for a in range(3, 9, 3):
            Nexser.write(('t' + str(position + a) + '.bco=' + str(63488)).encode())
            Nexser.write(end)  # k - структура b'xff' или же char(255)


end = struct.pack('3B', 0xff, 0xff, 0xff)  # Окончание посылок в Serial

Nexser = serial.Serial(  # Объект управляющий передачей данных по UART
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
TPH = []
for i in [temperature, pressure, humidity]:  # Если status поля OFF, значит поле не нужно и мы его выключаем
    if i.status == 'ON':
        TPH.append(i)  # Включить в массив опрашиваемых ПЛК. Если не включать, то связи с ПЛК создано не буедт
    else:
        Nexser.write(('t' + str(i.C_type + 3) + '.txt=""').encode())  # Убираем надпись
        Nexser.write(end)  # end - структура b'xff' или же char(255)
        for a in range(3, 9, 3):  # Заполняем голубым цветом ныне пустое поле
            Nexser.write(('t' + str(i.C_type + a) + '.bco=' + str(11676)).encode())
            Nexser.write(end)

node = SAIANode(lid=253)  # Создаём объект node

servers = []

for i, parameter in enumerate(TPH):
    servers.append(node.servers.declare(parameter.C_IP))  # Создание объекта server в памяти устройства
    servers[i].setReadOnly()  # Настройка возможности только приёма информации с PCD без возможности изменения
    servers[i].memory.flags.declare(index=parameter.flag)  # Флаг, на опрашиваемом PCD
    servers[i].memory.registers.declare(index=parameter.reg)  # Регистр, на опрашиваемом PCD
node.sleep(1)

while node.isRunning():  # Пока всё работает нормально (нет прерываний, ошибок)
    try:  # Пока нет ошибок запускаем опрос всех объектов servers (PCD)
        for server, parameter in zip(servers, TPH):
            if not server.isAlive():  # Если нет связанных серверов, попытаться подключиться и настроить параметры
                # Зачем я так делал я не помню, но помогало в каких-то ситуациях. Заново настраиваем параметры
                server.setReadOnly()
                server.memory.flags.declare(index=parameter.flag)
                server.memory.registers.declare(index=parameter.reg)
            if server.status != 82:  # Если состояние Run, то пишем данные. Если PCD попадёт в режим Halted или Error
                change_color(parameter.C_type, 1)  # Меняем цвет на красный и
                change_value(parameter.C_type, "*")  # Выводим звёздочки на экран
            else:  # Сервер активен и находится в режиме Run
                change_color(parameter.C_type, server.flags[parameter.flag].value)
                change_value(parameter.C_type, server.memory.registers[parameter.reg].int10)
        node.refresh()  # Запрос в Сеть на обновление значений всех регистров и флагов для всех серверов
        node.sleep(0.5)  # Не меняем параметры в течение 500 мс
    except:  # Если появляется ошибка, выключаем плату
        node.close()
        break
