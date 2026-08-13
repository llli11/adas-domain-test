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
-- Table structure for table `tool_requirement`
--

DROP TABLE IF EXISTS `tool_requirement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tool_requirement` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `tool_name` varchar(100) NOT NULL COMMENT '工具名称',
  `tool_type` varchar(50) NOT NULL COMMENT '工具类型',
  `specification` varchar(200) DEFAULT NULL COMMENT '规格型号',
  `quantity` int NOT NULL DEFAULT '1' COMMENT '需求数量',
  `requester_id` int NOT NULL COMMENT '需求人ID',
  `requester_name` varchar(50) NOT NULL COMMENT '需求人姓名',
  `request_date` datetime(6) NOT NULL COMMENT '需求日期',
  `reason` longtext COMMENT '需求原因',
  `status` varchar(20) NOT NULL DEFAULT '待处理' COMMENT '状态: 待处理/已采购/已拒绝',
  `handler_id` int DEFAULT NULL COMMENT '处理人ID',
  `handler_name` varchar(50) DEFAULT NULL COMMENT '处理人姓名',
  `handle_time` datetime(6) DEFAULT NULL COMMENT '处理时间',
  `remark` longtext COMMENT '备注',
  PRIMARY KEY (`id`),
  KEY `idx_tool_requir_created_43e1a8` (`created_at`),
  KEY `idx_tool_requir_updated_1c2fcf` (`updated_at`),
  KEY `idx_tool_requir_tool_na_77fc2d` (`tool_name`),
  KEY `idx_tool_requir_tool_ty_8a73ff` (`tool_type`),
  KEY `idx_tool_requir_request_1ac3c9` (`requester_id`),
  KEY `idx_tool_requir_request_c3fabc` (`request_date`),
  KEY `idx_tool_requir_status_3b59ba` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tool_requirement`
--

LOCK TABLES `tool_requirement` WRITE;
/*!40000 ALTER TABLE `tool_requirement` DISABLE KEYS */;
/*!40000 ALTER TABLE `tool_requirement` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:51
