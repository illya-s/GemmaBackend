# Backend API Endpoints

## User Authentication & Session Management

### Request Code for Login
- **Method:** POST
- **Endpoint:** `/api/user/auth/request/`
- **Description:** Запрос кода входа на email
- **Request Body:**
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response:** 
  ```json
  {
    "message": "Код отправлен на email"
  }
  ```
- **Status:** 200 OK

### Enter Code (Login)
- **Method:** POST
- **Endpoint:** `/api/user/auth/enter/`
- **Description:** Вход по коду подтверждения
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "code": "123456"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Вы вошли!",
    "user": {
      "username": "username",
      "email": "user@example.com",
      "avatar": "url_or_null"
    },
    "access_token": "token_string"
  }
  ```
- **Status:** 200 OK
- **Cookie:** `refresh` (httponly)

### Refresh Access Token
- **Method:** POST
- **Endpoint:** `/api/user/auth/refresh/`
- **Description:** Обновление access токена через refresh token
- **Headers:** Cookie содержит `refresh` токен
- **Response:**
  ```json
  {
    "access_token": "new_token_string"
  }
  ```
- **Status:** 200 OK

### Get Current Session
- **Method:** GET
- **Endpoint:** `/api/user/auth/session/`
- **Description:** Получение информации о текущем пользователе
- **Authentication:** Required (Bearer Token)
- **Response:**
  ```json
  {
    "id": 1,
    "uid": "unique_id",
    "username": "username",
    "email": "user@example.com",
    "avatar": "url_or_null"
  }
  ```
- **Status:** 200 OK

---

## Device Management

### Get Active Devices
- **Method:** GET
- **Endpoint:** `/api/user/devices/`
- **Description:** Получение списка активных устройств пользователя
- **Authentication:** Required (Bearer Token)
- **Response:**
  ```json
  [
    {
      "id": 1,
      "device_id": "device_uuid",
      "user_agent": "Mozilla/5.0...",
      "ip_address": "192.168.1.1",
      "created_at": "2024-12-09T10:00:00Z",
      "expires_at": "2024-12-10T10:00:00Z"
    }
  ]
  ```
- **Status:** 200 OK

### Delete Specific Device (Logout)
- **Method:** DELETE
- **Endpoint:** `/api/user/devices/<id>/`
- **Description:** Выход с конкретного устройства
- **Authentication:** Required (Bearer Token)
- **Response:**
  ```json
  {
    "detail": "Device logged out successfully"
  }
  ```
- **Status:** 200 OK

### Logout From Other Devices
- **Method:** POST
- **Endpoint:** `/api/user/devices/logout_others/`
- **Description:** Выход со всех других устройств, кроме текущего
- **Authentication:** Required (Bearer Token)
- **Request Body:**
  ```json
  {
    "device_id": "current_device_uuid"
  }
  ```
- **Response:**
  ```json
  {
    "detail": "All other devices logged out"
  }
  ```
- **Status:** 200 OK

---

## Authentication Classes & Permissions

- **RequestCodeView:** AllowAny
- **EnterCodeView:** AllowAny
- **RefreshView:** JWTAuthentication
- **SessionView:** IsAuthenticated
- **DeviceListView:** IsAuthenticated
- **DeviceDeleteView:** IsAuthenticated
- **DeviceLogoutOthersView:** IsAuthenticated

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid token" | "Refresh token expired"
}
```

### 404 Not Found
```json
{
  "detail": "Device not found"
}
```

### 500 Internal Server Error
```json
{
  "message": "Error message"
}
```
