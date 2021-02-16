debug = False
trace = False

"""CPU functionality."""

import sys

nullByte = 0b00000000

#region Instruction set
HLT  = 0b00000001
PRN  = 0b01000111
LDI  = 0b10000010
#endregion Instruction set

class CPU:
    """Main CPU class."""

    #region init
    def __init__(self):
        """Construct a new CPU."""
        if debug: print(f"nullByte:\t{bin(nullByte)}")

        #region Registers
        self.registers = [nullByte for r in range(8)]
        #region General Purpose Registers documentation
        """
        General Purpose Registers
        8 general-purpose 8-bit numeric registers R0-R7.

        - R5 is reserved as the interrupt mask (IM)
        - R6 is reserved as the interrupt status (IS)
        - R7 is reserved as the stack pointer (SP)

        These registers only hold values between 0-255.
        After performing math on registers in the emulator, bitwise-AND the result with 0xFF (255) to keep the register values in that range.
        """
        #endregion General Purpose Registers documentation
        self.IM = 5     # interrupt mask (IM)
        self.IS = 6     # interrupt status (IS)
        self.SP = 7     # stack pointer (SP)
        if debug: print(f"registers:\t{self.registers}")
        #endregion Registers

        #region Internal Registers
        self.PC  = 0            # Program Counter, address of currently executing instruction
        self.IR  = nullByte     # Instruction Register, contains a copy of the currently executing instruction
        self.MAR = nullByte     # Memory Address Register, holds the memory address we're reading or writing
        self.MDR = nullByte     # Memory Data Register, holds the value to write or the value just read
        self.FL  = nullByte     # Flags register FL holds the current flags status.
        #region Flags Register documentation
        """
        The flags register FL holds the current flags status. These flags can change based on the operands given to the CMP opcode.
        The register is made up of 8 bits. If a particular bit is set, that flag is "true".

        FL bits: 00000LGE

        - L = Less-than: during a CMP, set to 1 if registerA is less than registerB, zero otherwise.
        - G = Greater-than: during a CMP, set to 1 if registerA is greater than registerB, zero otherwise.
        - E = Equal: during a CMP, set to 1 if registerA is equal to registerB, zero otherwise.
        """
        #endregion Flags Register documentation
        #endregion Internal Registers

        #region Memory
        self.RAM = [nullByte] * 256
        if debug: print(f"RAM ({len(self.RAM)}) bytes:\n{self.RAM}")
        #region Memory documentation
        """ Memory
        The LS-8 has 8-bit addressing, so can address 256 bytes of RAM total.

        Memory map:

            top of RAM
        +-----------------------+
        | FF  I7 vector         |    Interrupt vector table
        | FE  I6 vector         |
        | FD  I5 vector         |
        | FC  I4 vector         |
        | FB  I3 vector         |
        | FA  I2 vector         |
        | F9  I1 vector         |
        | F8  I0 vector         |
        | F7  Reserved          |
        | F6  Reserved          |
        | F5  Reserved          |
        | F4  Key pressed       |    Holds the most recent key pressed
        | F3  Start of Stack    |
        | F2  [more stack]      |    Stack grows down
        | ...                   |
        | 01  [more program]    |
        | 00  Program entry     |    Program loaded upward in memory starting at 0
        +-----------------------+
            bottom of RAM
        """
        #endregion Memory documentation
        #endregion Memory

        #region Stack
        self.registers[self.SP] = 0xF4
        #region Stack documentation
        """
        The SP points at the value at the top of the stack (most recently pushed), or at address F4 if the stack is empty.
        """
        #endregion Stack documentation
        #endregion Stack


        #region Interrupts

        #region Interrupts documentation
        """ Interrupts
        There are 8 interrupts, I0-I7.

        When an interrupt occurs from an external source or from an INT instruction, the appropriate bit in the IS register will be set.

        Prior to instruction fetch, the following steps occur:

        The IM register is bitwise AND-ed with the IS register and the results stored as maskedInterrupts.
        Each bit of maskedInterrupts is checked, starting from 0 and going up to the 7th bit, one for each interrupt.
        If a bit is found to be set, follow the next sequence of steps. Stop further checking of maskedInterrupts.
        If a bit is set:

        Disable further interrupts.
        Clear the bit in the IS register.
        The PC register is pushed on the stack.
        The FL register is pushed on the stack.
        Registers R0-R6 are pushed on the stack in that order.
        The address (vector in interrupt terminology) of the appropriate handler is looked up from the interrupt vector table.
        Set the PC is set to the handler address.
        While an interrupt is being serviced (between the handler being called and the IRET), further interrupts are disabled.

        See IRET, below, for returning from an interrupt.

        Interrupt numbers
        0: Timer interrupt. This interrupt triggers once per second.
        1: Keyboard interrupt. This interrupt triggers when a key is pressed. The value of the key pressed is stored in address 0xF4.
        """
        #endregion Interrupts documentation
        #endregion Interrupts

        #region Power On State documentation
        """
        When the LS-8 is booted, the following steps occur:

        R0-R6 are cleared to 0.
        R7 is set to 0xF4.
        PC and FL registers are cleared to 0.
        RAM is cleared to 0.
        Subsequently, the program can be loaded into RAM starting at address 0x00.
        """
        #endregion Power On State documentation

    #endregion init

    def ram_read(self, address):
        self.MAR = address
        self.MDR = self.RAM[self.MAR]
        if debug: print(f"ram_read({self.MAR}) = {self.MDR}")
        return self.MDR

    def ram_write(self, address, value):
        self.MAR = address
        self.MDR = value
        if debug: old = self.RAM[self.MAR]
        self.RAM[self.MAR] = self.MDR
        if debug:
            new = self.RAM[self.MAR]
            print(f"ram_write({self.MAR}, {self.MDR}); was: {old}, is: {new}")

    #region Load
    def load(self):
        """Load a program into memory."""

        address = 0

        # For now, we've just hardcoded a program:

        program = [
            # From print8.ls8
            0b10000010, # LDI R0,8
            0b00000000,
            0b00001000,
            0b01000111, # PRN R0
            0b00000000,
            0b00000001, # HLT
        ]

        for instruction in program:
            self.RAM[address] = instruction
            address += 1
    #endregion Load

    #region ALU
    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")
    #endregion ALU

    #region Trace
    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.PC,
            #self.FL,
            #self.IE,
            self.ram_read(self.PC),
            self.ram_read(self.PC + 1),
            self.ram_read(self.PC + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.registers[i], end='')

        print()
    #endregion Trace

    #region Run
    def run(self):
        """Run the CPU."""
        if debug: print("running")
        running = True

        while running:
            self.IR = self.ram_read(self.PC)

            if self.IR == HLT:
                # HLT
                """
                Halt the CPU (and exit the emulator).
                """
                if debug: print(f"HLT")
                running = False

            elif self.IR == LDI:
                # LDI register immediate
                """
                Set the value of a register to an integer.
                """
                self.PC += 1
                reg_idx = self.ram_read(self.PC)
                self.PC += 1
                value = self.ram_read(self.PC)
                if debug: print(f"LDI R{reg_idx} {value}")
                self.registers[reg_idx] = value

            elif self.IR == PRN:
                # PRN register (pseudo-instruction)
                """
                Print numeric value stored in the given register.
                Print to the console the decimal integer value that is stored in the given register.
                """
                self.PC += 1
                reg_idx = self.ram_read(self.PC)
                number = self.registers[reg_idx]
                if debug: print(f"PRN R{reg_idx}")
                print(int(number))

            else:
                print(f"Unimplemented command: {self.IR}")
                running = False

            self.PC += 1

            if trace: self.trace()
    #endregion Run
