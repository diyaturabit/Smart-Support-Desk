db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "supportdesk"
}

"""CREATE TABLE ticket (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,

    status ENUM('Open', 'Inprogress', 'Closed') 
        NOT NULL DEFAULT 'Open',

    priority ENUM('Low', 'Medium', 'High') 
        NOT NULL DEFAULT 'Medium',

    customer_id INT NOT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME 
        DEFAULT CURRENT_TIMESTAMP 
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_ticket_customer
        FOREIGN KEY (customer_id) REFERENCES customer(id)
        ON DELETE CASCADE
);
"""



"""CREATE TABLE customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) NOT NULL UNIQUE,
    age INT,
    email VARCHAR(120) NOT NULL UNIQUE,
    company VARCHAR(120) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP 
        DEFAULT CURRENT_TIMESTAMP 
        ON UPDATE CURRENT_TIMESTAMP
);
"""

"""CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('staff', 'admin') NOT NULL DEFAULT 'staff',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP 
        DEFAULT CURRENT_TIMESTAMP 
        ON UPDATE CURRENT_TIMESTAMP
);
"""


"""CREATE TABLE login_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email VARCHAR(255),
    role VARCHAR(50),
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),

    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""