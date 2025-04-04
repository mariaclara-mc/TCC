faturamento = 1200 #tipo de variavel int -> numero inteiro
custo = 750  #tipo float -> número com casa decimal
novas_vendas = 100
faturamento = faturamento + novas_vendas
imposto = faturamento*0.1 #10% de imposto
lucro = faturamento - custo 
margem_lucro = lucro / faturamento


print("o faturamento foi de", faturamento)
print("o custo foi de", custo)
print("o lucro foi de", lucro- imposto)
print(" a margem de lucro foi de", round(margem_lucro, 1)) #arrendoda um numero para determinadas casa decimais
mensagem = "o faturamento da loja foi de: " #tipo string -> texto

teve_lucro = True #varaivel tipo boolian

#mod -> % resto da divisão
print (10 %3  )

tempo_contrato = 170 #meses
tempo_ano = 170/12 
print("o tempo do contrato em ano é", tempo_ano)
tempo_meses = 170 % 12
print("o tempo em meses é de", tempo_meses )