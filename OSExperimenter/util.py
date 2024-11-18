#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
* Author: Zongjian Yang
* Date: 2024/10/6 下午5:54 
* Project: OSExperimenter 
* File: util.py
* IDE: PyCharm 
* Function: 编写独立于实验内容本身的函数或数据结构
"""
import random
random.seed(42)


class UniqueStack:
    """用于完成实验二中LRU页面置换算法实现所用到的特殊栈结构。"""
    def __init__(self, init: list, capacity=3):
        self.stack = init
        self.set = set(init)
        self.capacity = capacity

    def push(self, value) -> None:
        """
        入栈操作。特别地，若入栈元素已存在，则移动到栈顶; 若栈已满则弹出栈底元素。
        :param value: 入栈元素
        :return: None
        """
        if value in self.set:  # 如果元素已存在
            self.stack.remove(value)  # 从栈中移除该元素
        elif len(self.stack) >= self.capacity:  # 如果栈已满
            bottom_element = self.stack.pop(0)  # 移除栈底元素
            self.set.remove(bottom_element)  # 从集合中移除栈底元素

        self.stack.append(value)  # 将新元素放入栈顶
        self.set.add(value)  # 将新元素添加到集合中

    def pop(self):
        """出栈操作"""
        if not self.is_empty():
            value = self.stack.pop()
            self.set.remove(value)
            return value
        raise IndexError("栈为空！")

    def bottom(self):
        """返回栈底元素"""
        if not self.is_empty():
            return self.stack[0]
        raise IndexError("栈为空！")

    def is_empty(self):
        """判断栈是否为空"""
        return len(self.stack) == 0

    def __len__(self):
        """返回栈的大小"""
        return len(self.stack)

    def __str__(self):
        """打印栈的内容"""
        return str(self.stack)


class Bit:
    def __init__(self):
        self.val = random.randint(0, 255)

    def get(self, idx: int) -> int:
        """
        获得字节某位的值
        :param idx: 位置（位），从低到高
        :return: 0或1
        """
        return 1 if (self.val >> idx) & 1 else 0

    def free(self, idx: int) -> None:
        """
        释放内存，将1改为0
        :param idx: 内存块所在位置的字节位
        :return: None
        """
        self.val &= ~(1 << idx)

    def use(self, idx: int) -> None:
        """
        使用内存，将0改为1
        :param idx: 内存块所在位置的字节位
        :return: None
        """
        self.val |= 1 << idx

    def __str__(self) -> str:
        """将字节转换为八位二进制形式的字符串"""
        return format(self.val, '08b')
