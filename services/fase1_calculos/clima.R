# Desativar a notação científica para uma apresentação mais limpa
options(scipen = 999)

# Instalar os pacotes se ainda não tiver feito
install.packages("httr2")
install.packages("jsonlite")

# Carregar os pacotes
library(httr2)
library(jsonlite)

# --- 1. Análise Estatística das Áreas de Cultivo ---

# Coletar os dados simulados a partir da lógica do código Python
# Esses dados representam exemplos de áreas em hectares que seriam inseridas pelo usuário.
areas_cafe <- c(10.5, 12.3, 8.8, 15.1, 9.7)
areas_cana <- c(35.2, 41.5, 38.9, 45.0, 32.1)

# Análise Estatística para Café
resumo_cafe <- summary(areas_cafe)
media_cafe <- mean(areas_cafe)
desvio_padrao_cafe <- sd(areas_cafe)

# Análise Estatística para Cana-de-açúcar
resumo_cana <- summary(areas_cana)
media_cana <- mean(areas_cana)
desvio_padrao_cana <- sd(areas_cana)

# Análise Combinada (opcional)
todas_as_areas <- c(areas_cafe, areas_cana)
resumo_total <- summary(todas_as_areas)
media_total <- mean(todas_as_areas)
desvio_padrao_total <- sd(todas_as_areas)

# Formatar e imprimir a saída da análise estatística
saida <- sprintf(
  "### Análise Estatística para Cultivo de Café ###
* Média de área: %.2f hectares
* Desvio padrão: %.2f hectares
* Resumo:
    * Mínimo: %.2f hectares
    * 1º Quartil: %.2f hectares
    * Mediana: %.2f hectares
    * 3º Quartil: %.2f hectares
    * Máximo: %.2f hectares

---

### Análise Estatística para Cultivo de Cana-de-açúcar ###
* Média de área: %.2f hectares
* Desvio padrão: %.2f hectares
* Resumo:
    * Mínimo: %.2f hectares
    * 1º Quartil: %.2f hectares
    * Mediana: %.2f hectares
    * 3º Quartil: %.2f hectares
    * Máximo: %.2f hectares

---

### Análise Estatística para Todas as Culturas Juntas ###
* Média de área total: %.2f hectares
* Desvio padrão total: %.2f hectares
* Resumo:
    * Mínimo: %.2f hectares
    * 1º Quartil: %.2f hectares
    * Mediana: %.2f hectares
    * 3º Quartil: %.2f hectares
    * Máximo: %.2f hectares
",
  media_cafe, desvio_padrao_cafe, resumo_cafe[1], resumo_cafe[2], resumo_cafe[3], resumo_cafe[5], resumo_cafe[6],
  media_cana, desvio_padrao_cana, resumo_cana[1], resumo_cana[2], resumo_cana[3], resumo_cana[5], resumo_cana[6],
  media_total, desvio_padrao_total, resumo_total[1], resumo_total[2], resumo_total[3], resumo_total[5], resumo_total[6]
)

cat(saida)

# Adicionar uma linha de separação para clareza
cat("\n\n####################################################\n\n")

# --- 2. Análise de Condições Climáticas em Tempo Real ---

# A API Open-Meteo usa coordenadas de latitude e longitude.
# Coordenadas para São Paulo, Brasil.
lat <- -23.5505
lon <- -46.6333

# Construir a URL da API
api_url <- paste0(
  "https://api.open-meteo.com/v1/forecast?latitude=",
  lat,
  "&longitude=",
  lon,
  "&current=temperature_2m,relative_humidity_2m&timezone=America%2FSao_Paulo"
)

# Inicializar a variável para garantir que ela exista fora do tryCatch
api_response <- NULL

# Fazer a requisição GET
# Usamos tryCatch para lidar com possíveis erros de conexão
api_response <- tryCatch(
  {
    request(api_url) %>%
      req_perform()
  },
  error = function(e) {
    message("Erro ao conectar à API: ", e$message)
    return(NULL)
  }
)

# Verificar se a resposta da API é válida
if (!is.null(api_response)) {
  # Converter o conteúdo da resposta de JSON para uma lista em R
  data <- fromJSON(resp_body_string(api_response))
  
  # Extrair os dados de temperatura e umidade
  temp <- data$current$temperature_2m
  humidity <- data$current$relative_humidity_2m
  
  # Exibir as informações no console
  cat("--- Dados Meteorológicos para São Paulo ---\n")
  cat(paste("Data e Hora:", data$current$time, "\n"))
  cat(paste("Temperatura:", temp, "°C\n"))
  cat(paste("Umidade Relativa:", humidity, "%\n"))
  cat("--------------------------------------------\n")
  cat("\n")
  
  # Análise para o cultivo de café
  cat("--- Análise para o Cultivo de Café ---\n")
  if (temp >= 18 && temp <= 22 && humidity >= 70) {
    cat("Condições MUITO favoráveis para o cultivo de café.\n")
  } else if (temp >= 15 && temp <= 30 && humidity >= 60) {
    cat("Condições favoráveis para o cultivo de café.\n")
  } else {
    cat("Condições NÃO ideais para o cultivo de café. O café prefere temperaturas amenas e umidade mais alta.\n")
  }
  cat("----------------------------------------\n")
  cat("\n")
  
  # Análise para o cultivo de cana-de-açúcar
  cat("--- Análise para o Cultivo de Cana-de-Açúcar ---\n")
  if (temp >= 20 && temp <= 30 && humidity >= 50) {
    cat("Condições MUITO favoráveis para o cultivo de cana-de-açúcar.\n")
  } else if (temp > 15 && temp < 35 && humidity >= 40) {
    cat("Condições favoráveis para o cultivo de cana-de-açúcar.\n")
  } else {
    cat("Condições NÃO ideais para o cultivo de cana-de-açúcar. A cana-de-açúcar prefere temperaturas mais altas e boa umidade.\n")
  }
  cat("--------------------------------------------------\n")
  
} else {
  # Mensagem caso a requisição falhe
  cat("Não foi possível obter dados meteorológicos.\n")
}