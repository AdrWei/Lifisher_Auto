library(httr)
library(jsonlite)
  
  tryCatch({
  ## 环境变量
  lifisher_codes <- Sys.getenv("LIFISHER_CODES")
  lifisher_token <- Sys.getenv("LIFISHER_TOKEN")
  lifisher_variables <- Sys.getenv("LIFISHER_VARIABLES")
  lifisher_staff_codes <- Sys.getenv("LIFISHER_STAFF_CODES")
  
  # 解析 JSON
  codes <- fromJSON(lifisher_codes)
  token_parts <- fromJSON(lifisher_token)
  constants <- fromJSON(lifisher_variables)
  AGENTS <- fromJSON(lifisher_staff_codes)
  
  # 提取 JSON 中的值
  USERNAME <- codes$USERNAME
  PASSWORD <- codes$PASSWORD
  APPKEY <- codes$APPKEY
  
  ## 重组 TOKEN
  TOKEN <- paste0(token_parts$Token_1, token_parts$Token_2, token_parts$Token_3, token_parts$Token_4)
  
  # 常量定义
  LOGIN_URL <- constants$LOGIN_URL
  INQUIRY_LIST_URL <- constants$INQUIRY_LIST_URL
  ASSIGN_URL <- constants$ASSIGN_URL
  User_Agent <- constants$User_Agent
  DOMAIN <- constants$DOMAIN
  REFERER <- constants$REFERER
  SITE_ID <- constants$SITE_ID
  X_Trace_Id <- constants$X_Trace_Id
    
}, error = function(e) {
  print(paste("Error:", e$message))
})

# 1. 登录平台，获取 token 和 cookies ----
login_response <- GET(
  LOGIN_URL,
  config(ssl_verifypeer = FALSE),
  query = list(
    username = "USERNAME",
    password = "PASSWORD"
  ),
  user_agent("Mozilla/5.0")
)

  # 提取 token
  login_data <- content(login_response, "parsed")
  token <- login_data$token  # 假设 token 在登录响应中
  
  # 提取 cookies
  cookies_df <- cookies(login_response)
  cookies_vec <- paste(cookies_df$name, cookies_df$value, sep = "=")
  cookies_header <- paste(cookies_vec, collapse = "; ")
  
  # 2. 获取最新询盘列表----
  inquiry_list_url <- INQUIRY_LIST_URL
  
  # 请求参数（根据抓包信息添加）
  inquiry_list_params <- list(
    return_source = 1,
    is_junk = 0,
    site_id = 5735,
    page_size = 200,
    page_number = 1,
    status = 0,
    sort = "create_time desc"
  )

# 请求头
  inquiry_list_headers <- add_headers(
    `User-Agent` = User_Agent,
    `appkey` = APPKEY,
    `token` = TOKEN,
    `domain` = DOMAIN,
    `Referer` = REFERER,
    `timestamp` = as.character(as.numeric(Sys.time()) * 1000),
    `X-Trace-Id` = X_Trace_Id
  )
  
  # 发送 GET 请求
  inquiry_list_response <- GET(
    inquiry_list_url,
    config(ssl_verifypeer = FALSE),
    inquiry_list_headers,
    query = inquiry_list_params
  )
    
    # 解析询盘列表
    inquiry_list_data <- content(inquiry_list_response, "parsed")

    # 获取筛选后的未分配询盘列表----
     #检查是否有询盘数据
     if (!is.null(inquiry_list_data$data$list)) {
       # 提取询盘数据
       inquiry_list <- inquiry_list_data$data$list
       
       # 检查是否有数据
       if (!is.null(inquiry_list) && length(inquiry_list) > 0) {
         # 提取询盘 ID
         inquiry_ids <- sapply(inquiry_list, function(x) x$id)  # 假设 id 是询盘 ID 的字段名
         print("提取的询盘 ID：")
         print(inquiry_ids)
       } else {
         print("所有询盘均已分配")
         return()
       }
     } else {
       print("未找到询盘数据字段，请检查响应数据结构。")
     }
        
    #开始询盘分配 ----
    # 请求头（使用与获取询盘列表相同的请求头）
    assign_headers <- add_headers(
      `User-Agent` = User_Agent,
      `appkey` = APPKEY,
      `token` = TOKEN,
      `domain` = DOMAIN,
      `Referer` = REFERER,
      `timestamp` = as.character(as.numeric(Sys.time()) * 1000),
      `X-Trace-Id` = X_Trace_Id
    )
                              
    # 将询盘列表平均分配给两个业务员
    for (i in seq_along(inquiry_ids)) {
      # 随机选择一个业务员
      assign_to <- as.character(sample(AGENTS, 1))
      
      # 请求体（使用正确的字段名称和 JSON 编码）
       body <- list(
        id = as.character(inquiry_ids[i]),
        client_account_id = as.character(assign_to),
        site_id = as.character(SITE_ID)
      )
      
      # 发送 POST 请求
      assign_response <- POST(
        ASSIGN_URL,
        config(ssl_verifypeer = FALSE),
        assign_headers,
        body = body,
        encode = "json"
      )}
