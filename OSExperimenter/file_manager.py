#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
* Author: Zongjian Yang
* Date: 2024/11/4 上午10:31 
* Project: OSExperimenter 
* File: file_manager.py
* IDE: PyCharm 
* Function: OS实验三 文件与磁盘管理
"""
import os
import struct
from datetime import datetime


class FCB:
    def __init__(self, name: str, file_type: str, size: int = 0):
        if file_type not in {"DIR", "FILE"}:
            raise ValueError("file_type must be 'DIR' or 'FILE'")

        self.name = name  # 文件或目录名
        self.size = size  # 文件或目录大小，目录默认为0
        self.file_type = file_type  # 文件类型：DIR 或 FILE
        self.time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 创建时间
        self.next = None  # 下一个兄弟节点
        self.child = None  # 孩子节点
        self.parent = None  # 父节点

    def is_dir(self):
        return self.file_type == "DIR"


class FileManager:
    def __init__(self):
        self.root = FCB("root", "DIR")  # 根目录
        self.current_dir = self.root

    def md(self, name):
        """创建目录"""
        if self._find(name):
            print(f"Directory '{name}' already exists.")
            return
        new_dir = FCB(name, "DIR")
        new_dir.parent = self.current_dir
        self.insert_child(new_dir)
        print(f"Directory '{name}' created.")

    def mk(self, name, size=0):
        """创建文件"""
        if self._find(name):
            print(f"File '{name}' already exists.")
            return
        new_file = FCB(name, "FILE", size)
        new_file.parent = self.current_dir
        self.insert_child(new_file)
        print(f"File '{name}' created.")

    def cd(self, name):
        """切换目录"""
        if name == "..":
            if self.current_dir.parent:
                self.current_dir = self.current_dir.parent
            return
        target = self._find(name)
        if target and target.is_directory():
            self.current_dir = target
        else:
            print(f"Directory '{name}' not found.")

    def rd(self, name):
        """删除目录"""
        target = self._find(name)
        if target and target.is_directory() and not target.child:
            self.remove_child(target)
            print(f"Directory '{name}' removed.")
        else:
            print(f"Cannot remove directory '{name}'. It may not be empty or does not exist.")

    def del_file(self, name):
        """删除文件"""
        target = self._find(name)
        if target and not target.is_directory():
            self.remove_child(target)
            print(f"File '{name}' deleted.")
        else:
            print(f"File '{name}' not found.")

    def dir(self):
        """列出当前目录内容"""
        child = self.current_dir.child
        if not child:
            print("Directory is empty.")
            return
        while child:
            print(f"{child.name} ({'DIR' if child.is_dir() else 'FILE'}, "
                  f"{child.size}B) - Created at {child.time}")
            child = child.next

    # 辅助方法
    def _find(self, name):
        """在当前目录下查找文件或目录"""
        child = self.current_dir.child
        while child:
            if child.name == name:
                return child
            child = child.next
        return None

    def insert_child(self, node):
        """将节点插入到当前目录的孩子链表中"""
        if not self.current_dir.child:
            self.current_dir.child = node
        else:
            child = self.current_dir.child
            while child.next:
                child = child.next
            child.next = node

    def remove_child(self, node):
        """从当前目录的孩子链表中移除节点"""
        if self.current_dir.child == node:
            self.current_dir.child = node.next
        else:
            prev = self.current_dir.child
            while prev and prev.next != node:
                prev = prev.next
            if prev:
                prev.next = node.next


# 定义块大小和块数
BLOCK_SIZE = 256
BLOCK_COUNT = 8
DISK_FILE = "virtual_disk.bin"

# FAT表特殊标记
EMPTY_BLOCK = 0x0000
LAST_BLOCK = 0xFFFF


# 定义FAT表和虚盘文件
class FATFileSystem:
    def __init__(self):
        self.fat = [EMPTY_BLOCK] * BLOCK_COUNT  # 初始化FAT表
        self.disk_file = open(DISK_FILE, "wb+")
        self.init_disk()
        self.current_directory = 0  # 根目录起始块号
        self.create_time = datetime.now().strftime("%Y/%m/%d %H:%M")

    def init_disk(self):
        """初始化虚盘文件和根目录"""
        # 创建FAT表和空块
        if os.path.getsize(DISK_FILE) < BLOCK_SIZE * BLOCK_COUNT:
            # 设置根目录块为占用状态
            self.fat[0] = LAST_BLOCK
            # 初始化空块
            for _ in range(BLOCK_COUNT):
                self.disk_file.write(b'\x00' * BLOCK_SIZE)
            self.write_fat()
            print("Disk initialized with FAT table and root directory.")

    def write_fat(self):
        """将FAT表写入虚盘的前16字节"""
        self.disk_file.seek(0)
        for entry in self.fat:
            self.disk_file.write(struct.pack("H", entry))

    def allocate_block(self):
        """分配一个空闲块"""
        for i in range(BLOCK_COUNT):  # 从块1开始查找
            if self.fat[i] == EMPTY_BLOCK:
                self.fat[i] = LAST_BLOCK
                self.write_fat()
                return i
        raise RuntimeError("No free blocks available.")

    def release_block_chain(self, start_block):
        """释放一个块链表（文件或目录占用的所有块）"""
        while start_block != LAST_BLOCK:
            next_block = self.fat[start_block]
            self.fat[start_block] = EMPTY_BLOCK
            start_block = next_block
        self.write_fat()

    def write_block(self, block_no, data):
        """将数据写入指定块的空闲区域"""
        if len(data) != 32:
            raise ValueError("Data must be exactly 32 bytes to fit in a file control block.")

        # 计算块位置并跳过FAT表区域
        self.disk_file.seek(block_no * BLOCK_SIZE + 16)
        current_data = self.disk_file.read(BLOCK_SIZE)

        # 查找块内的第一个空闲32字节位置
        for i in range(0, BLOCK_SIZE, 32):
            if current_data[i:i + 32] == b'\x00' * 32:  # 空闲区域
                self.disk_file.seek(block_no * BLOCK_SIZE + 16 + i)
                self.disk_file.write(data)
                return

        raise ValueError("No free space in the block to write data.")

    def write_block2(self, block_no, data):
        """将数据写入指定块"""
        if len(data) != BLOCK_SIZE:
            raise ValueError(f"Data must be exactly {BLOCK_SIZE} bytes to fit in a block.")

        # 定位到块的起始位置，并写入整个块的数据
        self.disk_file.seek(block_no * BLOCK_SIZE + 16)
        self.disk_file.write(data)

    def read_block(self, block_no):
        """读取指定块的数据"""
        self.disk_file.seek(block_no * BLOCK_SIZE + 16)
        return self.disk_file.read(BLOCK_SIZE)

    @staticmethod
    def create_fcb(name, size, file_type, first_block, parent_block):
        """创建32字节的FCB结构（文件控制块），增加parent_block字段"""
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        fcb_data = struct.pack("8sIHHH14s", name.encode(), size, first_block, file_type, parent_block,
                               datetime_str.encode())
        return fcb_data

    @staticmethod
    def parse_fcb(fcb_data):
        """解析32字节的FCB结构"""
        name, size, first_block, file_type, parent_block, datetime_str = struct.unpack("8sIHHH14s", fcb_data)
        return name.decode().strip('\x00'), size, first_block, file_type, parent_block, datetime_str.decode().strip(
            '\x00')

    def md(self, name):
        """创建目录，记录父目录块号"""
        block_no = self.allocate_block()
        fcb = self.create_fcb(name, BLOCK_SIZE, 2, block_no, self.current_directory)
        self.write_block(self.current_directory, fcb)
        print(f"Directory '{name}' created at block {block_no}.")

    def mk(self, name, size):
        """创建文件"""
        # 获取当前目录的父块号
        data = self.read_block(self.current_directory)
        fcb_data = data[:32]  # 假设当前目录的第一个FCB记录了父目录信息
        _, _, _, _, parent_block, _ = self.parse_fcb(fcb_data)

        # 分配块并创建文件的FCB，使用当前目录的父块号
        block_no = self.allocate_block()
        fcb = self.create_fcb(name, size, 1, block_no, parent_block=parent_block)

        # 将文件的FCB写入当前目录的块
        self.write_block(self.current_directory, fcb)
        print(f"File '{name}' created with size {size} bytes at block {block_no}.")

    def cd(self, name):
        """切换目录，支持cd ..返回上一级"""
        if name == "..":  # 返回上一级目录
            if self.current_directory == 0:
                print("Already at the root directory.")
                return
            # 获取当前目录的父块号
            data = self.read_block(self.current_directory)
            fcb_data = data[:32]  # 假设第一个 FCB 是当前目录的 FCB
            _, _, _, _, parent_block, _ = self.parse_fcb(fcb_data)
            self.current_directory = parent_block
            print("Moved up to the parent directory.")
        else:
            # 查找当前目录中的子目录
            block_no = self.find_block_by_name(name, file_type=2)
            if block_no is not None:
                self.current_directory = block_no
                print(f"Changed directory to '{name}' (block {block_no}).")
            else:
                print(f"Directory '{name}' not found.")

    def rd(self, name):
        """删除空目录"""
        # 找到目录的块号
        block_no = self.find_block_by_name(name, file_type=2)
        if block_no is None:
            print(f"Directory '{name}' not found.")
            return

        # 检查目录是否为空
        data = self.read_block(block_no)
        if any(data[i:i + 32].strip(b'\x00') for i in range(0, BLOCK_SIZE, 32)):
            print(f"Directory '{name}' is not empty.")
            return

        # 释放目录块的 FAT 表记录
        self.release_block_chain(block_no)

        # 从父目录块中删除该目录的 FCB 信息
        parent_block_no = self.get_parent_block_no(block_no)
        if parent_block_no is not None:
            self.remove_fcb_from_directory(parent_block_no, name, file_type=2)

        print(f"Directory '{name}' deleted.")

    def get_parent_block_no(self, block_no):
        """获取指定目录的父块号"""
        data = self.read_block(block_no)
        fcb_data = data[:32]  # 假设第一个 FCB 记录了当前目录的元信息
        _, _, _, _, parent_block, _ = self.parse_fcb(fcb_data)
        return parent_block

    def remove_fcb_from_directory(self, parent_block_no, name, file_type):
        """从父目录中删除指定名称和类型的 FCB 记录"""
        data = self.read_block(parent_block_no)
        new_data = bytearray(data)

        for i in range(0, BLOCK_SIZE, 32):
            fcb_data = data[i:i + 32]
            if fcb_data.strip(b'\x00'):
                fcb_name, _, _, fcb_type, _, _ = self.parse_fcb(fcb_data)
                if fcb_name == name and fcb_type == file_type:
                    # 清空该 FCB 记录
                    new_data[i:i + 32] = b'\x00' * 32
                    break

        # 将更新后的数据写回父目录块
        self.write_block2(parent_block_no, bytes(new_data))

    def del_file(self, name):
        """删除文件"""
        # 找到文件的块号
        block_no = self.find_block_by_name(name, file_type=1)
        if block_no is None:
            print(f"File '{name}' not found.")
            return

        # 释放文件块的 FAT 表记录
        self.release_block_chain(block_no)

        # 从父目录块中删除该文件的 FCB 信息
        self.remove_fcb_from_directory(self.current_directory, name, file_type=1)

        print(f"File '{name}' deleted.")

    def dir(self):
        """列出当前目录内容，格式化输出"""
        data = self.read_block(self.current_directory)
        print(f"{self.create_time}    <DIR>    .")
        print(f"{self.create_time}    <DIR>    ..")

        for i in range(0, len(data), 32):
            fcb_data = data[i:i + 32]
            if fcb_data.strip(b'\x00'):  # 过滤空的 FCB 数据
                name, size, first_block, file_type, _, datetime_str = self.parse_fcb(fcb_data)
                type_str = "<DIR>" if file_type == 2 else "     "
                size_str = "" if file_type == 2 else f"{size} B"
                date_time = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
                date_str = date_time.strftime('%Y/%m/%d %H:%M') if isinstance(date_time, datetime) else datetime_str

                # 输出每一行信息
                print(f"{date_str}    {type_str}    {name:<15} {size_str}")

    def find_block_by_name(self, name, file_type):
        """在当前目录查找指定名称的文件或目录块号"""
        data = self.read_block(self.current_directory)
        for i in range(0, len(data), 32):  # 遍历32字节单位
            fcb_data = data[i:i + 32]
            if fcb_data.strip(b'\x00'):
                fcb_name, _, first_block, fcb_type, _, _ = self.parse_fcb(fcb_data)
                if fcb_name == name and fcb_type == file_type:
                    return first_block
        return None

    def info(self, block_no=None):
        """显示虚盘的 FAT 表及指定块的内容"""
        # 显示 FAT 表内容
        for i, entry in enumerate(self.fat):
            if i % 8 == 0:
                print(f"{i:08X} ", end="")
            print(f"{entry:02X} ", end="")

        # 如果提供了 block_no，则显示该块的内容
        if block_no is not None:
            print()
            data = self.read_block(block_no)
            for i in range(0, len(data), 16):
                # 显示块中的数据，以16字节为一行
                print(f"{i:08X} ", end="")
                hex_data = " ".join(f"{b:02X}" for b in data[i:i + 16])
                ascii_data = "".join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i + 16])
                print(f"{hex_data:<48} {ascii_data}")

    def close(self):
        """关闭文件系统"""
        self.disk_file.close()


def console():
    fs = FATFileSystem()
    print("Welcome to the FAT File System Console (type 'help' for commands)")

    while True:
        # 显示当前目录路径
        current_path = f"\\{fs.current_directory}"
        command = input(f"{current_path}> ").strip().lower()

        # 解析命令
        if command.startswith("md "):
            name = command[3:].strip()
            fs.md(name)
        elif command.startswith("mk "):
            parts = command[3:].split()
            if len(parts) == 1:
                fs.mk(parts[0], 0)
            elif len(parts) == 2 and parts[1].isdigit():
                fs.mk(parts[0], int(parts[1]))
            else:
                print("Usage: MK filename [size]")
        elif command.startswith("cd "):
            name = command[3:].strip()
            fs.cd(name)
        elif command.startswith("rd "):
            name = command[3:].strip()
            fs.rd(name)
        elif command.startswith("del "):
            name = command[4:].strip()
            fs.del_file(name)
        elif command == "dir":
            fs.dir()
        elif command == "exit":
            print("Exiting the FAT File System Console...")
            fs.close()
            break
        elif command == "help":
            print_help()
        elif command.startswith("info"):
            block_no = int(command.split()[1]) if len(command.split()) > 1 else fs.current_directory
            fs.info(block_no)
        else:
            print(f"'{command}' is not recognized as a command. Type 'help' for a list of commands.")


def get_path(directory):
    """获取当前目录的路径"""
    path = []
    while directory:
        path.append(directory.name)
        directory = directory.parent
    return "\\".join(reversed(path))


def print_help():
    """显示帮助信息"""
    print("\nAvailable Commands:")
    print("MD dirname       - Create a new directory")
    print("MK filename [size] - Create a new file with optional size")
    print("CD dirname       - Change directory")
    print("CD ..            - Go up one directory level")
    print("RD dirname       - Remove an empty directory")
    print("DEL filename     - Delete a file")
    print("DIR              - List contents of the current directory")
    print("INFO [block_no]  - Display FAT table and block contents")
    print("EXIT             - Exit the file system\n")


if __name__ == '__main__':
    # fs = FATFileSystem()
    # fs.md("testdir")  # 创建目录
    # fs.mk("testfile", 512)  # 创建文件
    # fs.dir()  # 列出当前目录内容
    # fs.cd("testdir")  # 切换到子目录
    # fs.mk("test", 411)  # 创建文件
    # fs.dir()  # 列出子目录内容
    # fs.cd("..")  # 返回根目录
    # fs.info(0)
    # fs.dir()  # 列出子目录内容
    # fs.rd("testdir")  # 删除目录
    # fs.del_file("testfile")  # 删除文件
    # fs.close()

    console()
