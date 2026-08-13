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
-- Table structure for table `contractor_resignation`
--

DROP TABLE IF EXISTS `contractor_resignation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contractor_resignation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `staff_id` int NOT NULL COMMENT '人员ID',
  `application_date` datetime(6) DEFAULT NULL COMMENT '申请日期',
  `expected_date` datetime(6) DEFAULT NULL COMMENT '预计离职日期',
  `actual_date` datetime(6) DEFAULT NULL COMMENT '实际离职日期',
  `reason` longtext COMMENT '离职原因',
  `handover_status` varchar(50) DEFAULT NULL COMMENT '交接状态',
  `approval_status` varchar(20) NOT NULL DEFAULT '待审批' COMMENT '审批状态',
  `approver` varchar(50) DEFAULT NULL COMMENT '审批人',
  `approval_date` datetime(6) DEFAULT NULL COMMENT '审批日期',
  `remark` longtext COMMENT '备注',
  PRIMARY KEY (`id`),
  KEY `idx_contractor__created_a7b513` (`created_at`),
  KEY `idx_contractor__updated_3eb601` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='外委离职表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contractor_resignation`
--

LOCK TABLES `contractor_resignation` WRITE;
/*!40000 ALTER TABLE `contractor_resignation` DISABLE KEYS */;
/*!40000 ALTER TABLE `contractor_resignation` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:33
