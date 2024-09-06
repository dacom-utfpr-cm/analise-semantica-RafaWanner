inteiro: n
flutuante: x, y, z

inteiro fatorial(inteiro: n, flutuante: m)
	{NOTAÇÃO CIENTÍFICA}
	{WARNING: 'm' ESTÁ RECEBENDO VALORES DE TIPOS DIFERENTES}
	m := 5
	
	se n>0 então
		retorna(n)
	senão
		repita 
			flutuante: p
		até n = 0
	fim
	
	z := 1.9 {SEM ERRO, FOI INICIALIZADO}
	z := z+1 {ERRO, ID NAO FOI INICIALIZADO}

	{WARNING DE RETORNO: PASSANDO TIPO DIFERENTE}
	retorna(m)
fim

inteiro principal()
	leia(n)
	escreva(fatorial(1, 1.0)) {TIPOS DOS PARAMETROS DIFERENTES, TESTAR E VER SE ACUSA UM WARNING}
fim

{VERIFICAR SE A VARIÁVEL 'a' ESTÁ NO ESCOPO 'global'}

inteiro: a
flutuante: b

inteiro fatorial2(inteiro: fat, flutuante: fat2, inteiro: fat3)
	{VERIFICAÇÃO DE ATRIBUIÇÃO}

	a := 1
	{WARNING: 'a' = 'inteiro' -> ESTÁ RECEBENDO 'flutuante'}
	
	{SEM WARNING}
	

	{CHAMADA DE FUNÇÃO UMA DENTRO DA OUTRA!}
	escreva(fatorial(fatorial(1, 1.0), 1.0))

	a := fatorial(1, 1.0)

	{WARNING: VARIÁVEL 'b' é 'flutuante' E A FUNÇÃO È 'inteiro'}
	b := fatorial(1, 1.0)

	{CHAMADA DE FUNÇÃO NORMAL}
	fatorial(1, 1.0)
fim