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
-- Table structure for table `expense_supplier_rate`
--

DROP TABLE IF EXISTS `expense_supplier_rate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expense_supplier_rate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `name` varchar(50) NOT NULL COMMENT '供应商名称',
  `local_rate` decimal(10,2) NOT NULL DEFAULT '0.00' COMMENT '本地单价',
  `trip_rate` decimal(10,2) NOT NULL DEFAULT '0.00' COMMENT '出差单价',
  `unit` varchar(10) NOT NULL DEFAULT 'hour' COMMENT '单位: hour/day',
  `effective_to` date DEFAULT NULL COMMENT '生效截止日期（含），NULL 表示无截止',
  `code_trip` varchar(50) DEFAULT NULL COMMENT '出差服务编号',
  `effective_from` date DEFAULT NULL COMMENT '生效起始日期（含）',
  `code_local` varchar(50) DEFAULT NULL COMMENT '未出差服务编号',
  `contract_no` varchar(100) DEFAULT NULL COMMENT '合同号',
  PRIMARY KEY (`id`),
  KEY `idx_expense_sup_created_d32e3e` (`created_at`),
  KEY `idx_expense_sup_updated_95b2a9` (`updated_at`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='供应商单价';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expense_supplier_rate`
--

LOCK TABLES `expense_supplier_rate` WRITE;
/*!40000 ALTER TABLE `expense_supplier_rate` DISABLE KEYS */;
INSERT INTO `expense_supplier_rate` VALUES (1,'2026-07-08 11:24:56.000000','2026-07-08 11:41:26.000000','达安',160.00,160.00,'hour','2026-03-31',NULL,NULL,NULL,NULL),(5,'2026-07-08 11:41:26.000000','2026-07-08 11:41:26.000000','达安',130.00,130.00,'hour',NULL,NULL,'2026-04-01',NULL,NULL),(6,'2026-07-08 11:41:26.000000','2026-07-15 14:21:53.000000','育喆',250.00,330.00,'day',NULL,'RWYF0549061','2026-07-01','RWYF0549060','DFH-DS00093-CC2501'),(7,'2026-07-08 11:41:26.000000','2026-07-15 14:21:53.000000','育喆',290.00,356.00,'day','2026-06-30','RWYF0549061',NULL,'RWYF0549060','DFH-DS00093-CC2501'),(8,'2026-07-08 11:41:26.000000','2026-07-08 11:41:26.000000','驰恒',250.00,330.00,'day',NULL,NULL,'2026-07-01',NULL,NULL),(9,'2026-07-08 11:41:26.000000','2026-07-08 11:41:26.000000','驰恒',290.00,356.00,'day','2026-06-30',NULL,NULL,NULL,NULL),(10,'2026-07-08 11:41:26.000000','2026-07-15 14:21:53.000000','万嘉禾',281.00,356.00,'day',NULL,'RWYF0549073',NULL,'RWYF0549072','DFH-DS00094-CC2501');
/*!40000 ALTER TABLE `expense_supplier_rate` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:50
