-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 10.82.77.87    Database: mydb_local
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `username` varchar(20) NOT NULL COMMENT '用户名称',
  `alias` varchar(30) DEFAULT NULL COMMENT '姓名',
  `email` varchar(255) NOT NULL COMMENT '邮箱',
  `phone` varchar(20) DEFAULT NULL COMMENT '电话',
  `password` varchar(128) DEFAULT NULL COMMENT '密码',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `is_superuser` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否为超级管理员',
  `last_login` datetime(6) DEFAULT NULL COMMENT '最后登录时间',
  `dept_id` int DEFAULT NULL COMMENT '部门ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_user_created_b19d59` (`created_at`),
  KEY `idx_user_updated_dfdb43` (`updated_at`),
  KEY `idx_user_usernam_9987ab` (`username`),
  KEY `idx_user_alias_6f9868` (`alias`),
  KEY `idx_user_email_1b4f1c` (`email`),
  KEY `idx_user_phone_4e3ecc` (`phone`),
  KEY `idx_user_is_acti_83722a` (`is_active`),
  KEY `idx_user_is_supe_b8a218` (`is_superuser`),
  KEY `idx_user_last_lo_af118a` (`last_login`),
  KEY `idx_user_dept_id_d4490b` (`dept_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'2026-06-29 18:14:11.934797','2026-08-10 17:01:58.842101','admin',NULL,'admin@admin.com',NULL,'$argon2id$v=19$m=65536,t=3,p=4$IWTMGUNIqVXq3XuPEQKglA$q0Cdzwd21GWx/QbtRA+SO9pWr+z13fyeiRSLI+DZ7lc',1,1,'2026-08-10 09:01:58.841977',1),(3,'2026-08-07 17:25:32.662773','2026-08-13 09:04:09.562443','user001',NULL,'test@voyah.com.cn',NULL,'$argon2id$v=19$m=65536,t=3,p=4$ak3J+T9njBFCqJXSuhciBA$/7w0dcc/Ko5vughvbun0jokEhTPGtkP98vGH12bMzDY',1,0,'2026-08-13 01:04:09.562318',1);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:41
