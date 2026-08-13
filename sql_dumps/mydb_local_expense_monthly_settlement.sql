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
-- Table structure for table `expense_monthly_settlement`
--

DROP TABLE IF EXISTS `expense_monthly_settlement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expense_monthly_settlement` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `year_month` varchar(7) NOT NULL COMMENT '结算月份(YYYY-MM)',
  `labor_cost` decimal(12,2) NOT NULL DEFAULT '0.00' COMMENT '人工费用',
  `advance_payment` decimal(12,2) NOT NULL DEFAULT '0.00' COMMENT '垫付费用',
  `total_amount` decimal(12,2) NOT NULL DEFAULT '0.00' COMMENT '总金额',
  `status` varchar(20) NOT NULL DEFAULT '待比对' COMMENT '状态: 待比对/已确认/有差异',
  `remark` longtext COMMENT '备注',
  `test_order_id` bigint NOT NULL COMMENT '所属试验单号',
  PRIMARY KEY (`id`),
  KEY `fk_expense__expense__7d22197b` (`test_order_id`),
  KEY `idx_expense_mon_created_305fd9` (`created_at`),
  KEY `idx_expense_mon_updated_3a5482` (`updated_at`),
  KEY `idx_expense_mon_year_mo_c4a2e3` (`year_month`),
  KEY `idx_expense_mon_status_df62f5` (`status`),
  CONSTRAINT `fk_expense__expense__7d22197b` FOREIGN KEY (`test_order_id`) REFERENCES `expense_test_order` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='月度结算';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expense_monthly_settlement`
--

LOCK TABLES `expense_monthly_settlement` WRITE;
/*!40000 ALTER TABLE `expense_monthly_settlement` DISABLE KEYS */;
INSERT INTO `expense_monthly_settlement` VALUES (1,'2026-07-16 17:29:21.000000','2026-07-16 17:29:37.000000','2026-07',0.00,0.00,0.00,'更正',NULL,119);
/*!40000 ALTER TABLE `expense_monthly_settlement` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:30
