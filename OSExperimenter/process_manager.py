#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
* Author: Zongjian Yang
* Date: 2024/9/14 下午4:15 
* Project: OSExperimenter
* File: process_manager.py
* IDE: PyCharm 
* Function: OS实验一 进程控制 & 实验二 分页式存储管理
"""
import datetime
import time
import random
import collections
from math import ceil
from util import UniqueStack, Bit

random.seed(42)
BLOCK_NUM = 64  # 内存块数
BLOCK_SIZE = PAGE_SIZE = 1024  # 块/页大小
BYTE_LENGTH = 8  # 位示图单位长度
INPUT_NUM = 3  # 程序被放入内存的块数


class PCB:
    def __init__(self, name: str, memory_size: int, pc: int = None):
        self.pid = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.name = name
        self.next = None
        self.memory_size = memory_size  # 进程所占空间
        self.state = '新建'  # 新建, 就绪, 执行, 阻塞, 完成
        self.pc = pc

        self.block_num = ceil(self.memory_size / BLOCK_SIZE)  # 进程所占内存块数
        self.page_table = [PageTable(no) for no in range(self.block_num)]  # 定义并初始化页表

    def display_page_table(self):
        """详细展示进程的页表"""
        print(f"\n进程 {self.name} 的页表如下：\n页号 块号 状态位P 置换区地址")
        for pt in self.page_table:
            print(pt)


class PageTable:
    def __init__(self, no: int, p=0, m=False):
        self.no = no  # 页号
        self.block = None  # 物理块号
        self.state = p  # 状态位
        self.visit_time = 0  # 访问字段
        self.dirty = m  # 修改位
        self.address = None  # 外存地址，若该页不在内存中，则为置换区位置(块号)

    def allot(self, blk: int) -> None:
        """
        初始分配内存时，页表表示的进程部分调入内存时调用。
        :param blk: 分配的块号
        :return: None
        """
        self.block = blk
        self.state = 1

    def extra_pos(self, replace_bitmap: list[Bit]) -> None:
        """
        初始分配内存时，页表表示的进程部分放入外部置换区时调用。
        :param replace_bitmap: 置换区位示图
        :return: None
        """
        self.state = 0
        for i in range(BLOCK_NUM // BYTE_LENGTH):
            for j in range(BYTE_LENGTH):
                if replace_bitmap[i].get(j) == 0:
                    replace_bitmap[i].use(j)
                    self.address = i * BYTE_LENGTH + 7 - j
                    return

    def swap_with(self, other) -> None:
        """
        页面置换时将两个页面的属性进行调换(block和address)
        :param other: 另一个 PageTable 对象
        :return: None
        """
        # 交换 block
        self.block, other.block = other.block, self.block
        # 交换 address
        self.address, other.address = other.address, self.address

    def __str__(self) -> str:
        """
        展示页表时调用。
        :return: 页号 块号 状态位P 置换区地址
        """
        return f"{self.no} {self.block} {self.state} {self.address}"

    def __repr__(self) -> str:
        """
        返回每个 PageTable 对象的可读字符串表示，类似于 __str__，但用于列表等情景
        """
        return f"({self.no} {self.block} {self.state} {self.address})"


class ProcessManager:
    def __init__(self):
        self.ready_head = None      # 就绪队列
        self.blocked_head = None    # 阻塞队列
        self.finished_head = None   # 结束队列
        self.running = None         # 运行进程
        self.bitmap = [Bit() for _ in range(BLOCK_NUM // BYTE_LENGTH)]
        self.replace_bitmap = [Bit() for _ in range(BLOCK_NUM * 2 // BYTE_LENGTH)]
        self.pc = 0  # 指令计数器

        print('欢迎使用OS进程管理系统！      杨宗健20221543')
        print("计算机的初始内存使用情况如下所示（位示图）:")
        for idx, bit in enumerate(self.bitmap):
            print(f"第{idx}字节  {bit}")
        print("\n置换区（位示图）:")
        for idx, bit in enumerate(self.replace_bitmap):
            print(f"第{idx}字节  {bit}")

    @staticmethod
    def add_to_queue(head: PCB, process: PCB) -> PCB:
        """
        将进程加入到特定的队列中（就绪或阻塞）
        :param head: 队列的队头
        :param process: 进程对象
        :return: 队列的队头或进程对象
        """
        process.state = '就绪'
        if head is None:
            return process
        else:
            current = head
            while current.next:
                current = current.next
            current.next = process
        return head

    @staticmethod
    def locate_block(block_no: int) -> tuple:
        """
        获得页表物理块号对应的bitmap位置(字节, 位)。
        :param block_no:
        :return: (字节, 位)
        """
        return block_no // BYTE_LENGTH, 7 - block_no % BYTE_LENGTH

    def allocate_memory(self, process: PCB) -> PCB:
        """
        根据分页存储内存管理方法为进程分配内存空间。
        :param process: 进程对象。
        :return：如果分配成功，返回进程对象；如果分配失败，返回 None。
        """
        cnt = 0
        for i in range(BLOCK_NUM // BYTE_LENGTH):
            for j in range(BYTE_LENGTH):
                if self.bitmap[i].get(j) == 0:
                    if cnt < process.block_num and cnt < INPUT_NUM:
                        self.bitmap[i].use(j)
                        process.page_table[cnt].allot(i * BYTE_LENGTH + 7 - j)
                        cnt += 1
        if cnt == process.block_num:
            print(f"进程{process.name}内存分配成功！")
        else:
            # 剩余部分放入置换区
            for i in range(cnt, process.block_num):
                process.page_table[i].extra_pos(self.replace_bitmap)
        return process

    def create_process(self, name: str, size: int) -> None:
        """
        创建一个新进程，包括检查进程是否存在，内存分配，和进程控制块(PCB)的创建
        :param name: 进程的名称
        :param size: 进程所需的内存大小
        :return:
        """
        if self.process_exists(name):
            print(f"进程 {name} 已存在。")
            return

        # 尝试分配内存
        new_pcb = self.allocate_memory(PCB(name, size, self.pc + 1))
        if new_pcb is not None:
            # 成功分配内存后，增加指令计数器pc
            self.pc += 1
            # 如果已经有运行中的进程，将新进程添加到就绪队列
            if self.running is not None:
                self.ready_head = self.add_to_queue(self.ready_head, new_pcb)
                print(f"进程 {name} 已被创建并添加至就绪队列.")
            # 如果没有运行中的进程，即系统空闲，则直接运行新创建的进程
            else:
                self.running = new_pcb
                print(f'进程 {name} 已创建，并执行.')
        # 如果无法成功分配内存，打印错误信息
        else:
            print(f"无法为进程 {name} 分配内存，内存不足！")

    def free_memory(self, process: PCB) -> None:
        """
        释放进程的内存，将进程占用的内存块状态分别置 0
        """
        for page in process.page_table:
            if page.state == 1:
                i, j = self.locate_block(page.block)
                self.bitmap[i].free(j)
            else:
                i, j = self.locate_block(page.address)
                self.replace_bitmap[i].free(j)

    def locate_addr(self, logic_addr: int) -> int:
        """
        输入当前执行进程所要访问的逻辑地址，并将其转换成相应的物理地址.
        :param logic_addr: 逻辑地址
        :return: 物理地址
        """
        page_no = logic_addr // PAGE_SIZE
        offset = logic_addr % PAGE_SIZE
        if page_no > len(self.running.page_table):
            raise ValueError('地址越界！')
        return self.running.page_table[page_no].block * BLOCK_SIZE + offset

    def process_exists(self, name: str) -> bool:
        """
        检查系统中是否存在指定名称的进程。
        :param name: 需要检查的进程名称。
        :return:
             bool: 如果系统中存在指定名称的进程，则返回True；否则返回False。
        """
        # 检查就绪队列
        current = self.ready_head
        while current:
            if current.name == name:
                return True
            current = current.next

        # 检查阻塞队列
        current = self.blocked_head
        while current:
            if current.name == name:
                return True
            current = current.next

        # 检查正在执行的进程
        if self.running and self.running.name == name:
            return True

        return False

    def event_handler(self) -> None:
        """事件处理函数，用于根据用户输入执行相应的操作。"""
        while True:
            print('-' * 40)
            print("1. 创建进程\n"
                  "2. 执行时间片到\n"
                  "3. 阻塞进程\n"
                  "4. 唤醒进程\n"
                  "5. 结束进程\n"
                  "6. 根据逻辑地址定位物理地址\n"
                  "7. 置换算法模拟\n"
                  "8. 查看队列及内存\n"
                  "9. 通过demo预置测试程序\n"
                  "0. 退出")
            choice = input("键入命令: ")
            if choice == '1':
                name = input("进程名称: ")
                size = int(input("进程所需内存: "))
                self.create_process(name, size)
            elif choice == '2':
                self.execute_process()
            elif choice == '3':
                self.block_process()
            elif choice == '4':
                self.wake_process()
            elif choice == '5':
                self.terminate_process()
            elif choice == '6':
                print('正在运行的进程为', self.running.name)
                print(f"对应其在内存中的物理地址为：{self.locate_addr(int(input('要查询的逻辑地址：')))}")
            elif choice == '7':
                if not isinstance(self.running, PCB):
                    raise ValueError('当前没有正在运行的进程')
                alg = input("选择要执行的算法：FIFO[a]或LRU[b]")
                if alg.lower() == 'a':
                    self.FIFO()
                elif alg.lower() == 'b':
                    self.LRU()
                else:
                    print("非法命令，请重试！")
            elif choice == '8':
                self.show_queues_and_memory()
            elif choice == '9':
                self.demo_test()
            elif choice == '0':
                break
            else:
                print("非法命令，请重试！")

    def trans_running(self) -> None:
        """
        用于将就绪队列队头进程自动进入运行态。
        """
        self.running = None
        if self.ready_head is None:
            return
        self.running = self.ready_head
        if self.ready_head.next is not None:
            self.ready_head = self.ready_head.next
        else:
            self.ready_head = None
        self.running.next = None
        self.running.state = '执行'
        print(f"进程 {self.running.name} 正在运行...")

    def execute_process(self) -> None:
        """
        执行时间片到，将正在运行的进程进入就绪态。
        """
        if self.running:
            print(f"将进程 {self.running.name} 时间片到")
            self.ready_head = self.add_to_queue(self.ready_head, self.running)

            self.trans_running()  # 此时无正在运行的进程，应将就绪队列队头进程运行
        else:
            print('没有正在执行的进程')

    def block_process(self) -> None:
        """阻塞进程，将正在运行的进程进入阻塞队列，并轮转就绪队列队头运行。"""
        if self.running:
            self.running.state = '阻塞'
            self.blocked_head = self.add_to_queue(self.blocked_head, self.running)
            print(f"阻塞进程 {self.running.name} 并将其移动至阻塞队列.")

            self.trans_running()  # 此时无正在运行的进程，应将就绪队列队头进程运行
        else:
            print("没有进程可被阻塞.")

    def wake_process(self) -> None:
        """
        唤醒进程，将阻塞的进程重新加入到就绪队列中。
        """
        if self.blocked_head:
            process = self.blocked_head
            self.blocked_head = self.blocked_head.next
            process.next = None
            process.state = '就绪'
            self.ready_head = self.add_to_queue(self.ready_head, process)
            print(f"唤醒进程 {process.name} 并将其添加至就绪队列.")

            if self.running is None:
                self.trans_running()
        else:
            print("没有阻塞的进程等待唤醒.")

    def terminate_process(self) -> None:
        """杀死正在运行的的进程，并释放该进程所分配到的内存空间，轮转运行就绪队列队头。"""
        if self.running:
            print(f"正在结束进程 {self.running.name} ...")
            self.free_memory(self.running)

            self.trans_running()
        else:
            print("没有可被结束的进程.")

    def FIFO(self) -> None:
        """
        FIFO页面置换算法模拟，并计算缺页率和置换次数
        """
        deque = collections.deque(self.running.page_table[:3], maxlen=3)  # 创建进程时分配到内存的三个页表
        s = f = 0
        addr_seq = [random.randint(0, self.running.memory_size) for _ in range(5)]
        print(f"自动随机生成范围为[0, {self.running.memory_size}]、长度为10的进程逻辑地址序列：{addr_seq}")
        for addr in addr_seq:
            page_no, offset = addr // PAGE_SIZE, addr % PAGE_SIZE  # 页号 偏移量（页内地址）
            print("\n逻辑地址:", addr)
            print(f"逻辑地址{addr}对应的页号为 {page_no}，页内偏移地址为 {offset}")
            curr_page = self.running.page_table[page_no]
            # 若没有命中
            if curr_page.block is None:
                f += 1
                print(f"{page_no} 号页不存在于内存, 外存块号为{curr_page.address}，需置换...")
                pop_page = deque.popleft()
                deque.append(curr_page)
                print(f"\t利用FIFO算法选中内存队列0号页,该页内存块号为{pop_page.block}, 修改位为{pop_page.dirty},")
                print(f"\t内存 {pop_page.block} 号块内容写入置换区 {curr_page.address} 号块,")
                print(f"\t置换区 {curr_page.address} 内容写入内存 {pop_page.block} 号块--置换完毕！")
                curr_page.swap_with(pop_page)
            else:
                s += 1
                print(f"{page_no} 号页已存在于内存, 无需置换")
            print(f"逻辑地址{addr}对应的物理地址为:", self.locate_addr(addr))
        print(f"缺页率为{f / (s + f) * 100}%，交换次数为{f}")

    def LRU(self) -> None:
        """
        LRU页面置换算法模拟，并计算缺页率和置换次数。
        """
        stack = UniqueStack(self.running.page_table[:3])
        s = f = 0
        addr_seq = [random.randint(0, self.running.memory_size) for _ in range(5)]
        print(f"自动随机生成范围为[0, {self.running.memory_size}]、长度为10的进程逻辑地址序列：{addr_seq}")
        for addr in addr_seq:
            page_no, offset = addr // PAGE_SIZE, addr % PAGE_SIZE  # 页号 偏移量（页内地址）
            print("\n逻辑地址:", addr)
            print(f"逻辑地址{addr}对应的页号为 {page_no}，页内偏移地址为 {offset}")
            curr_page = self.running.page_table[page_no]
            # 若没有命中
            if curr_page.block is None:
                f += 1
                print(f"{page_no} 号页不存在于内存, 外存块号为{curr_page.address}，需置换...")
                pop_page = stack.bottom()
                print(f"\t利用LRU算法选中内存栈栈底页,该页内存块号为{pop_page.block}, 修改位为{pop_page.dirty},")
                print(f"\t内存 {pop_page.block} 号块内容弹出栈，写入置换区 {curr_page.address} 号块,")
                print(f"\t置换区 {curr_page.address} 内容入栈，写入内存 {pop_page.block} 号块--置换完毕！")
                curr_page.swap_with(pop_page)
            else:
                s += 1
                print(f"{page_no} 号页已存在于内存, 无需置换，将该页放在栈顶。")
            stack.push(curr_page)  # 入栈操作
            print(f"逻辑地址{addr}对应的物理地址为:", self.locate_addr(addr))
        print(f"缺页率为{f / (s + f) * 100}%，交换次数为{f}")

    def demo_test(self) -> None:
        """程序测试时设计的demo函数，可简便调试环节，节省进程创建时间。"""
        print('正在构建demo...')
        self.create_process(name='Music', size=1028)
        time.sleep(1)
        self.create_process(name='Vidio', size=10240)
        time.sleep(1)
        self.create_process(name='Print', size=4096)
        time.sleep(1)
        self.create_process(name='Game', size=10240)
        self.show_queues_and_memory()

    def show_queues_and_memory(self) -> None:
        # 就绪队列
        print("\n就绪队列:")
        print(f"{'名称':<10}{'大小':<10}{'PC值':<20}{'pid':<20}{'页表':<10}")
        current = self.ready_head
        while current:
            print(
                f"{current.name:<10}{current.memory_size:<10}{current.pc:<20}"
                f"{current.pid:<20}{str(current.page_table):<10}")
            current = current.next

        # 阻塞队列
        print("\n阻塞队列:")
        print(f"{'名称':<10}{'大小':<10}{'PC值':<20}{'pid':<20}{'页表':<10}")
        current = self.blocked_head
        while current:
            print(
                f"{current.name:<10}{current.memory_size:<10}{current.pc:<20}"
                f"{current.pid:<20}{str(current.page_table):<10}")
            current = current.next

        # 运行进程
        if self.running:
            print("\n运行进程:")
            print(f"{'名称':<10}{'大小':<10}{'PC值':<20}{'pid':<20}{'页表':<10}")
            print(
                f"{self.running.name:<10}{self.running.memory_size:<10}"
                f"{self.running.pc:<20}{self.running.pid:<20}{str(self.running.page_table):<10}")
        else:
            print("\n没有正在运行的进程.")

        # 内存空间
        print("\n内存空间（位示图）:")
        for idx, bit in enumerate(self.bitmap):
            print(f"第{idx}字节  {bit}")

        # 置换区
        print("\n置换区（位示图）:")
        for idx, bit in enumerate(self.replace_bitmap):
            print(f"第{idx}字节  {bit}")


if __name__ == '__main__':
    # 实例化并启动事件处理
    pm = ProcessManager()
    pm.event_handler()
