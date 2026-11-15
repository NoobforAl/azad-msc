# guest.S: the guest program of kvm-hello.c, for checking its bytes.
#   as --32 -o guest.o guest.S && objdump -d -mi8086 guest.o
	.code16
	.text
	mov  $0x3f8, %dx
	add  %bl, %al
	add  $'0', %al
	out  %al, (%dx)
	mov  $'\n', %al
	out  %al, (%dx)
	hlt
