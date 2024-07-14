import struct
from collections import OrderedDict

def main_app(hex_str):
    # hex_str = '47 24 1c 0a'
    # hex_str = '0a 1c 42 47'

    # hex_str = '42 0a'
    # hex_str = '47 1c'
    # hex_str = '1c'


    # hex_str = '42 0a 47 1c'

    # hex_word_list = [hex_str.replace(' ', '')[i:i+4] for i in range(0, len(hex_str.replace(' ', '')), 4)]
    # print(hex_word_list)


    # hex_byte_list_rev = hex_byte_list.copy()
    # hex_byte_list_rev.reverse()

    # hex_byte = bytes.fromhex(hex_str)

    # 高字在前
    # 低字在前
    # 高字节在前
    # 低字节在前

    hex_byte_list = [hex_str.replace(' ', '')[i:i+2] for i in range(0, len(hex_str.replace(' ', '')), 2)]

    type_dic = {
    'c':['char_bytes of length 1', '1', '长度为1的字节'],
    'b':['signed char_integer', '1', '整数的有符号'],
    'B':['unsigned char_integer', '1', '整数的无符号'],
    '?':['_Bool_bool', '1', '布尔值'],
    'h':['short_integer', '2', '短整数'],
    'H':['unsigned short_integer', '2', '无符号短整数'],
    'i':['int_integer', '4', '整数'],
    'I':['unsigned int_integer', '4', '无符号整数'],
    'l':['long_integer', '4', '长整数'],
    'L':['unsigned long_integer', '4', '无符号长整数'],
    'q':['long long_integer', '8', '长长整数'],
    'Q':['unsigned long long_integer', '8', '无符号长长整数'],
    'e':['half precision_float', '2', '半精度浮点数'],
    'f':['float_float', '4', '浮点数'],
    'd':['double_float', '8', '双精度浮点数'],
    }

    # for count in range(2):

    hex_byte = bytes.fromhex("".join(hex_byte_list))
    # 获取字节对象的长度
    byte_length = len(hex_byte)

    result_dict = OrderedDict()  # 使用 OrderedDict 确保顺序

    value = str(hex_byte_list).replace(',', ' ').replace('\'', '').replace('[', '').replace(']', '').upper()
    result_dict[f'原始值'] = value

    for i in type_dic:
        if type_dic[i][1] == str(byte_length):
            float_value_big_endian = struct.unpack(f'>{i}', hex_byte)[0]
            float_value_little_endian = struct.unpack(f'<{i}', hex_byte)[0]
            result_dict[f'{type_dic[i][2]}(大端)'] = float_value_big_endian
            result_dict[f'{type_dic[i][2]}(小端)'] = float_value_little_endian
                
        # hex_byte_list.reverse()

    return result_dict

    # x:pad                   byte no value
    # c:char                  bytes of length 1
    # b:signed                char 签名字符 integer 整数
    # B:unsigned              char 无符号字符 integer 整数
    # ?:_Bool                 bool 布尔值
    # h:short                 integer 整数
    # H:unsigned short        integer 整数
    # i:int                   integer 整数
    # I:unsigned int          integer 整数
    # l:long                  integer 整数
    # L:unsigned long         integer 整数
    # q:long long             integer 整数
    # Q:unsigned long long    integer 整数
    # n:ssize_t               integer 整数
    # N:size_t                integer 整数
    # e:(6)                   float 漂浮
    # f:float                 float 漂浮
    # d:double                float 漂浮
    # s:char[]                bytes 字节
    # p:char[]                bytes 字节
    # P:void*                 integer 整数



if __name__ == '__main__':
    print(main_app(hex_str='42 0a 47 1c'))

