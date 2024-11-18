#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
* Author: Zongjian Yang
* Date: 2024/11/9 下午5:03 
* Project: OSExperimenter 
* File: process_scheduler.py
* IDE: PyCharm 
* Function: OS实验四 进程调度
"""
import pandas as pd
from tabulate import tabulate


class PCB:
    def __init__(self, name: str, arrival_time: int, servicing_time: int,
                 priority: int = 0, max_r: list[int] = None, alloc: list[int] = None):
        self.name = name
        self.priority = priority  # 优先级
        self.arrival_time = arrival_time  # 到达时间
        self.servicing_time = servicing_time  # 服务时间
        self.running_time = 0  # 已运行时间
        self.finished_time = None  # 结束时间
        self.max = max_r or []  # 最大资源需求
        self.allocation = alloc  # 分配资源
        self.need = [max_r - alloc for max_r, alloc in zip(self.max, self.allocation)]  # 还需资源


class ProcessScheduler:
    def __init__(self, total_r: list[int]):
        self.process_list = []
        self.total_resources = total_r
        self.available = total_r[:]
        print('欢迎使用OS进程调度系统！             杨宗健20221543')

    def create_process(self):
        opt = input("是否手动创建进程？[Y/N]: ")
        if opt.lower() == 'y':
            n = int(input("输入进程个数: "))
            for i in range(n):
                name = input("进程名称: ")
                arrival_time = int(input(f"进程 {name} 的到达时间: "))
                servicing_time = int(input(f"进程 {name} 的服务时间: "))
                priority = int(input(f"进程 {name} 的优先级: "))
                max_r = [int(input(f"进程 {name} 的第{i + 1}类资源的最大需求: ")) for i in
                         range(len(self.total_resources))]
                allocation = [int(input(f"进程 {name} 的第{i + 1}类资源的预分配: ")) for i in
                              range(len(self.total_resources))]
                process = PCB(name, arrival_time, servicing_time, priority, max_r, allocation)
                self.process_list.append(process)
        else:
            file_path = 'Process_exp4.xlsx'
            try:
                # 读取Excel文件
                df = pd.read_excel(file_path)
                max_resource_cols = [col for col in df.columns if col.startswith("Max_resource")]
                allocation_cols = [col for col in df.columns if col.startswith("Allocation")]
                for _, row in df.iterrows():
                    name = row['Name']
                    arrival_time = row['Arrival_time']
                    servicing_time = row['Servicing_time']
                    priority = row['Priority']
                    max_r = [row[col] for col in max_resource_cols]
                    allocation = [row[col] for col in allocation_cols]

                    process = PCB(name, arrival_time, servicing_time, priority, max_r, allocation)
                    self.process_list.append(process)

                print(f"成功从文件 {file_path} 导入 {len(df)} 个进程")
                print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
            except Exception as e:
                print(f"读取Excel文件时发生错误: {e}")
        self.available = [self.total_resources[i] - sum(self.process_list[j].allocation[i]
                          for j in range(len(self.process_list))) for i in range(len(self.total_resources))]

    def FCFS(self) -> tuple[float, float]:
        """
        先来先服务(first come first server, FCFS)调度算法
        :return: 平均周转时间, 带权周转时间
        """
        # 先按到达时间排序
        self.process_list.sort(key=lambda x: x.arrival_time)

        current_time = 0  # 当前时刻
        total_turnaround_time = 0
        total_weighted_turnaround_time = 0

        for process in self.process_list:
            # 判断进程到达的时间与当前时刻的关系
            start_time = max(process.arrival_time, current_time)
            finish_time = start_time + process.servicing_time

            # 计算周转时间和带权周转时间
            process.finished_time = finish_time
            process.turnaround_time = finish_time - process.arrival_time
            process.weighted_turnaround_time = process.turnaround_time / process.servicing_time

            # 更新当前时刻
            current_time = finish_time

            # 累加周转时间和带权周转时间
            total_turnaround_time += process.turnaround_time
            total_weighted_turnaround_time += process.weighted_turnaround_time

        # 计算平均周转时间和平均带权周转时间
        avg_turnaround_time = total_turnaround_time / len(self.process_list)
        avg_weighted_turnaround_time = total_weighted_turnaround_time / len(self.process_list)

        # 输出结果
        self.print_results(avg_turnaround_time, avg_weighted_turnaround_time)
        return avg_turnaround_time, avg_weighted_turnaround_time

    def SJF(self) -> tuple[float, float]:
        """
        短作业优先 (Shortest Job First, SJF) 调度算法
        :return 平均周转时间, 带权周转时间
        """
        # 按到达时间排序，然后每次选择服务时间最短的进程
        ready_queue = []
        current_time = 0
        total_turnaround_time = 0
        total_weighted_turnaround_time = 0
        completed_processes = []

        # 按到达时间排序
        self.process_list.sort(key=lambda x: x.arrival_time)

        while self.process_list or ready_queue:
            # 将已到达且未执行的进程加入就绪队列
            while self.process_list and self.process_list[0].arrival_time <= current_time:
                ready_queue.append(self.process_list.pop(0))

            # 如果就绪队列中有进程，选择服务时间最短的一个
            if ready_queue:
                # 按服务时间排序，选择最短的进程
                ready_queue.sort(key=lambda x: x.servicing_time)
                process = ready_queue.pop(0)

                # 计算该进程的完成时间
                start_time = max(current_time, process.arrival_time)
                finish_time = start_time + process.servicing_time

                # 设置进程相关信息
                process.finished_time = finish_time
                process.turnaround_time = finish_time - process.arrival_time
                process.weighted_turnaround_time = process.turnaround_time / process.servicing_time

                # 更新当前时刻为该进程的完成时间
                current_time = finish_time

                # 记录累计的周转时间和带权周转时间
                total_turnaround_time += process.turnaround_time
                total_weighted_turnaround_time += process.weighted_turnaround_time

                # 将已完成的进程加入列表以便于显示
                completed_processes.append(process)
            else:
                # 当前无进程可以运行，时间前进
                current_time += 1

        # 更新已完成的进程列表
        self.process_list = completed_processes

        # 计算平均周转时间和平均带权周转时间
        avg_turnaround_time = total_turnaround_time / len(self.process_list)
        avg_weighted_turnaround_time = total_weighted_turnaround_time / len(self.process_list)

        # 输出结果
        self.print_results(avg_turnaround_time, avg_weighted_turnaround_time)
        return avg_turnaround_time, avg_weighted_turnaround_time

    def RR(self, time_quantum: int) -> tuple[float, float]:
        """
        轮转 (Round Robin, RR) 调度算法
        :param time_quantum: 轮转长度
        :return 平均周转时间, 带权周转时间
        """
        ready_queue = []
        current_time = 0
        total_turnaround_time = 0
        total_weighted_turnaround_time = 0
        completed_processes = []
        execute_seq = []

        # 将进程按到达时间排序
        self.process_list.sort(key=lambda x: x.arrival_time)

        # 初始阶段，将第一个到达的进程加入队列
        while self.process_list or ready_queue:
            # 将到达时间小于或等于当前时刻的进程加入到就绪队列
            while self.process_list and self.process_list[0].arrival_time <= current_time:
                ready_queue.append(self.process_list.pop(0))

            if ready_queue:
                # 从就绪队列取出第一个进程
                process = ready_queue.pop(0)

                # 判断该进程的剩余执行时间是否超过时间片
                execution_time = min(time_quantum, process.servicing_time - process.running_time)

                # 更新进程的运行时间和当前时刻
                process.running_time += execution_time
                current_time += execution_time
                execute_seq.append(process.name)

                # 在执行完一个时间片后，检查是否有新的进程到达
                while self.process_list and self.process_list[0].arrival_time <= current_time:
                    ready_queue.insert(0, self.process_list.pop(0))
                    # print('add ', ready_queue[-1].name)

                # 检查该进程是否完成
                if process.running_time == process.servicing_time:
                    process.finished_time = current_time
                    process.turnaround_time = process.finished_time - process.arrival_time
                    process.weighted_turnaround_time = process.turnaround_time / process.servicing_time

                    # 记录累计的周转时间和带权周转时间
                    total_turnaround_time += process.turnaround_time
                    total_weighted_turnaround_time += process.weighted_turnaround_time

                    # 将完成的进程加入已完成列表
                    completed_processes.append(process)
                else:
                    # 若进程未完成，则将其放回就绪队列的末尾
                    ready_queue.append(process)
            else:
                # 若无进程可执行，时间前进
                current_time += 1

        # 更新已完成的进程列表
        self.process_list = completed_processes

        # 计算平均周转时间和平均带权周转时间
        avg_turnaround_time = total_turnaround_time / len(self.process_list)
        avg_weighted_turnaround_time = total_weighted_turnaround_time / len(self.process_list)

        # 轮转执行进程的顺序
        print('进程执行顺序:', ''.join(execute_seq))

        # 输出结果
        self.print_results(avg_turnaround_time, avg_weighted_turnaround_time)
        return avg_turnaround_time, avg_weighted_turnaround_time

    def PS(self) -> tuple[float, float]:
        """
        优先级抢占调度 (Priority Scheduling, Preemptive) 算法
        :return 平均周转时间, 带权周转时间
        """
        ready_queue = []
        current_time = 0
        total_turnaround_time = 0
        total_weighted_turnaround_time = 0
        completed_processes = []
        execute_seq = []

        # 将进程按到达时间排序
        self.process_list.sort(key=lambda x: x.arrival_time)

        while self.process_list or ready_queue:
            # 将到达时间小于或等于当前时刻的进程加入到就绪队列
            while self.process_list and self.process_list[0].arrival_time <= current_time:
                ready_queue.append(self.process_list.pop(0))

            if ready_queue:
                # 按优先级和到达时间排序 (优先级高的在前，若优先级相同按到达时间先后)
                ready_queue.sort(key=lambda x: (x.priority, x.arrival_time))

                # 从就绪队列中选取优先级最高的进程
                process = ready_queue[0]

                # 执行当前进程一个时间单位
                process.running_time += 1
                current_time += 1
                execute_seq.append(process.name)

                # 检查进程是否完成
                if process.running_time == process.servicing_time:
                    process.finished_time = current_time
                    process.turnaround_time = process.finished_time - process.arrival_time
                    process.weighted_turnaround_time = process.turnaround_time / process.servicing_time

                    # 记录累计的周转时间和带权周转时间
                    total_turnaround_time += process.turnaround_time
                    total_weighted_turnaround_time += process.weighted_turnaround_time

                    # 将完成的进程移出就绪队列，并加入已完成列表
                    ready_queue.pop(0)
                    completed_processes.append(process)
            else:
                # 若无进程可执行，时间前进
                current_time += 1

        # 更新已完成的进程列表
        self.process_list = completed_processes

        # 计算平均周转时间和平均带权周转时间
        avg_turnaround_time = total_turnaround_time / len(self.process_list)
        avg_weighted_turnaround_time = total_weighted_turnaround_time / len(self.process_list)

        # 执行进程的顺序
        print('进程执行顺序:', ''.join(execute_seq))

        # 输出结果
        self.print_results(avg_turnaround_time, avg_weighted_turnaround_time)
        return avg_turnaround_time, avg_weighted_turnaround_time

    def HRRN(self) -> tuple[float, float]:
        """
        高响应比优先(Highest Response Ratio Next, HRRN)调度算法
        :return 平均周转时间, 带权周转时间
        """
        ready_queue = []
        current_time = 0
        total_turnaround_time = 0
        total_weighted_turnaround_time = 0
        completed_processes = []

        # 将进程按到达时间排序
        self.process_list.sort(key=lambda x: x.arrival_time)

        while self.process_list or ready_queue:
            # 将当前时间到达的所有进程加入到就绪队列
            while self.process_list and self.process_list[0].arrival_time <= current_time:
                ready_queue.append(self.process_list.pop(0))

            if ready_queue:
                # 计算每个进程的响应比，选择响应比最高的进程
                for process in ready_queue:
                    waiting_time = current_time - process.arrival_time
                    process.response_ratio = (waiting_time + process.servicing_time) / process.servicing_time

                # 按响应比降序排序，选择响应比最高的进程
                ready_queue.sort(key=lambda x: x.response_ratio, reverse=True)
                process = ready_queue.pop(0)

                # 执行选中的进程
                current_time += process.servicing_time
                process.finished_time = current_time
                process.turnaround_time = process.finished_time - process.arrival_time
                process.weighted_turnaround_time = process.turnaround_time / process.servicing_time

                # 累计总的周转时间和带权周转时间
                total_turnaround_time += process.turnaround_time
                total_weighted_turnaround_time += process.weighted_turnaround_time

                # 将执行完成的进程加入已完成列表
                completed_processes.append(process)
            else:
                # 如果没有进程可以执行，则时间前进
                current_time += 1

        # 更新已完成的进程列表
        self.process_list = completed_processes

        # 计算平均周转时间和平均带权周转时间
        avg_turnaround_time = total_turnaround_time / len(self.process_list)
        avg_weighted_turnaround_time = total_weighted_turnaround_time / len(self.process_list)

        # 输出结果
        self.print_results(avg_turnaround_time, avg_weighted_turnaround_time)
        return avg_turnaround_time, avg_weighted_turnaround_time

    def MFQ(self, time_slices: list[int] = None) -> tuple[float, float]:
        """
        多级反馈队列 (Multilevel Feedback Queue, MFQ) 调度算法
        :param time_slices: 不同队列的时间片长度
        :return 平均周转时间, 带权周转时间
        """
        if time_slices is None:
            time_slices = [1, 2, 4, 8]
        queues = [[] for _ in time_slices]  # 创建多级队列，每级队列对应一个时间片
        current_time = 0
        total_turnaround_time = 0
        total_weighted_turnaround_time = 0
        completed_processes = []

        # 将进程按到达时间排序
        self.process_list.sort(key=lambda x: x.arrival_time)

        # 开始调度
        while self.process_list or any(queues):
            # 将到达时间小于或等于当前时刻的进程加入到最高优先级队列
            while self.process_list and self.process_list[0].arrival_time <= current_time:
                queues[0].append(self.process_list.pop(0))

            # 查找当前非空的最高优先级队列
            for level, queue in enumerate(queues):
                if queue:
                    process = queue.pop(0)
                    time_slice = time_slices[level]
                    execution_time = min(time_slice, process.servicing_time - process.running_time)

                    # 执行当前进程一个时间片或直到完成
                    current_time += execution_time
                    process.running_time += execution_time

                    # 检查进程是否完成
                    if process.running_time == process.servicing_time:
                        process.finished_time = current_time
                        process.turnaround_time = process.finished_time - process.arrival_time
                        process.weighted_turnaround_time = process.turnaround_time / process.servicing_time

                        # 累计总的周转时间和带权周转时间
                        total_turnaround_time += process.turnaround_time
                        total_weighted_turnaround_time += process.weighted_turnaround_time

                        # 记录已完成的进程
                        completed_processes.append(process)
                    else:
                        # 未完成则降级到下一优先级队列
                        if level + 1 < len(queues):
                            queues[level + 1].append(process)
                        else:
                            queues[level].append(process)  # 若已在最低优先级队列则回到同级队列
                    break
            else:
                # 若所有队列为空且有未到达的进程，则推进时间
                current_time += 1

        # 更新已完成的进程列表
        self.process_list = completed_processes

        # 计算平均周转时间和平均带权周转时间
        avg_turnaround_time = total_turnaround_time / len(self.process_list)
        avg_weighted_turnaround_time = total_weighted_turnaround_time / len(self.process_list)

        # 输出结果
        self.print_results(avg_turnaround_time, avg_weighted_turnaround_time)
        return avg_turnaround_time, avg_weighted_turnaround_time

    def banker_request(self, process: PCB, request: list[int]) -> bool:
        """
        银行家算法资源请求
        :param process: 执行算法的进程
        :param request: 该进程的资源请求情况
        :return 是否处于安全状态
        """
        if all(req <= need and req <= avail for req, need, avail in
               zip(request, process.need, self.available)):
            # 试探性分配
            for i in range(len(request)):
                self.available[i] -= request[i]
                process.allocation[i] += request[i]
                process.need[i] -= request[i]

            # 安全性检查
            is_safe, seq = self.is_safe_state()
            if is_safe:
                print(f"请求成功：进程 {process.name} 分配资源 {request}")
                print(f"可以找到一个安全序列: {seq}")
                return True
            else:
                # 回退
                for i in range(len(request)):
                    self.available[i] += request[i]
                    process.allocation[i] -= request[i]
                    process.need[i] += request[i]
                print(f"请求失败：进程 {process.name} 的请求 {request} 导致不安全状态")
                return False
        else:
            print(f"请求不合法：进程 {process.name} 的请求 {request} 超过需求或可用资源")
            return False

    def is_safe_state(self) -> (bool, list):
        """安全性算法，检查当前系统是否处于安全状态，并返回安全序列，同时输出矩阵信息"""
        work = self.available[:]
        finish = [False] * len(self.process_list)
        safe_sequence = []

        # 用于存储每一轮执行时的详细状态
        status_log = []

        while True:
            found = False
            for i, process in enumerate(self.process_list):
                # 判断当前进程是否满足分配条件
                if not finish[i] and all(need <= work[j] for j, need in enumerate(process.need)):
                    # 记录当前状态
                    finish[i] = True
                    status_log.append({
                        "Process": process.name,
                        "Work": work[:],
                        "Need": process.need[:],
                        "Allocation": process.allocation[:],
                        "Work+Allocation": [work[j] + process.allocation[j] for j in range(len(work))],
                        "Finish": finish[:]
                    })

                    # 假设进程完成，释放资源
                    for j in range(len(work)):
                        work[j] += process.allocation[j]
                    safe_sequence.append(process.name)
                    found = True
                    break

            if not found:
                break

        # 判断系统是否安全，并输出每一轮状态
        if all(finish):
            print("系统处于安全状态。安全序列为:", safe_sequence)
            print("\n各轮次状态:")
            for log in status_log:
                print(f"\n进程: {log['Process']}")
                print(f"Work: {log['Work']}")
                print(f"Need: {log['Need']}")
                print(f"Allocation: {log['Allocation']}")
                print(f"Work+Allocation: {log['Work+Allocation']}")
                print(f"Finish: {log['Finish']}")
            return True, safe_sequence
        else:
            print("系统处于不安全状态，无法生成安全序列。")
            return False, []

    def print_results(self, avg_turnaround_time, avg_weighted_turnaround_time):
        print(f"{'进程名':<5}{'到达时间':<10}{'服务时间':<10}{'完成时间':<10}{'周转时间':<13}{'带权周转时间':<10}")
        for process in self.process_list:
            print(f"{process.name:<10}{process.arrival_time:<12}{process.servicing_time:<12}{process.finished_time:<12}"
                  f"{process.turnaround_time:<15}{process.weighted_turnaround_time:<20.4f}")

        print(f"\n平均周转时间: {avg_turnaround_time:.4f}")
        print(f"平均带权周转时间: {avg_weighted_turnaround_time:.4f}")

    def find_process(self, name: str):
        for pcb in self.process_list:
            if pcb.name == name:
                return pcb
        else:
            return None

    def console(self):
        while True:
            print('-' * 60)
            print("1. 创建进程\n"
                  "2. 先来先服务(FCFS)调度算法\n"
                  "3. 短作业优先(SJF)调度算法\n"
                  "4. 轮转(RR)调度算法\n"
                  "5. 优先级抢占(PSP)调度算法\n"
                  "6. 高响应比优先(HRRN)调度算法\n"
                  "7. 多级反馈队列(MFQ)调度算法\n"
                  "8. 银行家算法\n"
                  "0. 退出")
            choice = input("键入命令: ")
            if choice == '1':
                self.create_process()
            elif choice == '2':
                self.FCFS()
            elif choice == '3':
                self.SJF()
            elif choice == '4':
                time_quantum = int(input("请输入轮转长度: "))
                self.RR(time_quantum)
            elif choice == '5':
                self.PS()
            elif choice == '6':
                self.HRRN()
            elif choice == '7':
                self.MFQ()
            elif choice == '8':
                name = input("请输入执行算法的进程名称: ")
                process = self.find_process(name)
                if process:
                    req = [int(i) for i in input("请输入请求资源: ").split()]
                    self.banker_request(process, req)
                else:
                    print("进程不存在！")
            elif choice == '0':
                break
            else:
                print("非法命令，请重试！")


if __name__ == '__main__':
    scheduler = ProcessScheduler(total_r=[10, 5, 7])
    scheduler.console()
