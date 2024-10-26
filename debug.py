def d_print(func, str):
    print(f"(In {func}) {str}")
    with open('debug.txt', 'a') as f:
        f.write(f"(In {func}) {str}\n")

def d_error(func, str):
    print(f"(In {func}) Error: {str}")
    with open('debug.txt', 'a') as f:
        f.write(f"(In {func}) Error: {str}\n")