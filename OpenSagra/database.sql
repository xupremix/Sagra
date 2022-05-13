DROP TABLE IF EXISTS `composition`;

DROP TABLE IF EXISTS `dish`;

DROP TABLE IF EXISTS `location`;

DROP TABLE IF EXISTS `admin`;

DROP TABLE IF EXISTS `ingredient`;

CREATE TABLE IF NOT EXISTS `location` (
    `id` int NOT NULL AUTO_INCREMENT,
    `name` varchar(40) NOT NULL,
    `type` varchar(40) NOT NULL,
    PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `dish` (
    `id` int NOT NULL AUTO_INCREMENT,
    `name` varchar(40) NOT NULL,
    `description` varchar(100),
    `price` decimal(5, 2) NOT NULL,
    `day` varchar(9) NOT NULL,
    `location` int NOT NULL,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`location`) REFERENCES `location`(`id`)
);

CREATE TABLE IF NOT EXISTS `ingredient` (
    `id` int NOT NULL AUTO_INCREMENT,
    `name` varchar(40) NOT NULL,
    `availability` int NOT NULL,
    PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `composition` (
    `idDish` int NOT NULL,
    `idIngredient` int NOT NULL,
    `day` varchar(9) NOT NULL,
    `quantity` int NOT NULL,
    PRIMARY KEY (`idDish`, `idIngredient`, `day`),
    FOREIGN KEY (`idDish`) REFERENCES `dish`(`id`),
    FOREIGN KEY (`idIngredient`) REFERENCES `ingredient`(`id`)
);

CREATE TABLE IF NOT EXISTS `admin` (
    `id` int AUTO_INCREMENT,
    `username` VARCHAR(12) NOT NULL UNIQUE,
    `role` VARCHAR(12) NOT NULL,
    `password` CHAR(32) NOT NULL,
    PRIMARY KEY (`id`)
);
