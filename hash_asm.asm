; SHA-256 hash computation for Python integration
; Compile with: nasm -f elf64 hash_asm.asm -o hash_asm.o
; Link with: ld -shared -o libhash.so hash_asm.o

section .data
    ; SHA-256 constants (first 8 values)
    k: dq 0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5
        dq 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5

section .text
    global sha256_hash
    global sha256_init

; Function: sha256_hash(input_ptr, input_len, output_ptr)
; Input: rdi = input pointer, rsi = input length, rdx = output pointer
; Output: void (result written to output_ptr)
sha256_hash:
    push rbp
    mov rbp, rsp
    
    ; Save registers
    push rbx
    push r12
    push r13
    push r14
    push r15
    
    ; Initialize hash values (first 8 SHA-256 values)
    mov rax, 0x6a09e667
    mov [rdx], rax
    mov rax, 0xbb67ae85
    mov [rdx+4], rax
    mov rax, 0x3c6ef372
    mov [rdx+8], rax
    mov rax, 0xa54ff53a
    mov [rdx+12], rax
    mov rax, 0x510e527f
    mov [rdx+16], rax
    mov rax, 0x9b05688c
    mov [rdx+20], rax
    mov rax, 0x1f83d9ab
    mov [rdx+24], rax
    mov rax, 0x5be0cd19
    mov [rdx+28], rax
    
    ; Simple XOR-based hash (simplified for demo)
    mov rcx, rsi      ; counter = input length
    mov r8, rdi       ; input pointer
    mov r9, rdx       ; output pointer
    
hash_loop:
    cmp rcx, 0
    jle hash_done
    
    mov al, [r8]      ; load byte from input
    xor al, 0xAA      ; XOR with constant
    mov [r9], al      ; store in output
    
    inc r8
    inc r9
    dec rcx
    jmp hash_loop
    
hash_done:
    ; Restore registers
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    
    mov rsp, rbp
    pop rbp
    ret

; Function: sha256_init()
; Returns: void
sha256_init:
    ret
