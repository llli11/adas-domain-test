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
-- Table structure for table `expense_diff_record`
--

DROP TABLE IF EXISTS `expense_diff_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expense_diff_record` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `diff_description` longtext NOT NULL COMMENT '差异描述',
  `responsible_person` varchar(50) NOT NULL COMMENT '责任人',
  `status` varchar(20) NOT NULL DEFAULT '待处理' COMMENT '状态: 待处理/已处理',
  `handle_time` datetime(6) DEFAULT NULL COMMENT '处理时间',
  `remark` longtext COMMENT '备注',
  `settlement_id` bigint NOT NULL COMMENT '所属结算单',
  PRIMARY KEY (`id`),
  KEY `fk_expense__expense__8dd59c04` (`settlement_id`),
  KEY `idx_expense_dif_created_93aea3` (`created_at`),
  KEY `idx_expense_dif_updated_303672` (`updated_at`),
  KEY `idx_expense_dif_status_308230` (`status`),
  CONSTRAINT `fk_expense__expense__8dd59c04` FOREIGN KEY (`settlement_id`) REFERENCES `expense_monthly_settlement` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='差异记录';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expense_diff_record`
--

LOCK TABLES `expense_diff_record` WRITE;
/*!40000 ALTER TABLE `expense_diff_record` DISABLE KEYS */;
/*!40000 ALTER TABLE `expense_diff_record` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:36
