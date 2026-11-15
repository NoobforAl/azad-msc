# guest-mmio.S: guest for the Lab 06.4 extension. Loaded at guest-physical 0x1000.
#   as --32 -o g.o guest-mmio.S && ld -m elf_i386 -Ttext=0x1000 --oformat binary -o g.bin g.o && xxd -i g.bin
	.code16
	.text
	.globl _start
_start:
	mov  $0x3f8, %dx
	mov  $msg, %si          # DS = 0 in real mode after our sregs setup
1:	lodsb                   # al = [ds:si++]
	test %al, %al
	jz   2f
	out  %al, (%dx)         # one KVM_EXIT_IO per character
	jmp  1b
2:	movb $0x42, 0x8000      # no memory slot at 0x8000 -> KVM_EXIT_MMIO
	hlt
msg:	.asciz "Hello\n"
