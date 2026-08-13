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
-- Table structure for table `tool_inventory_detail`
--

DROP TABLE IF EXISTS `tool_inventory_detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tool_inventory_detail` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `inventory_id` int NOT NULL COMMENT '盘点任务ID',
  `tool_id` int NOT NULL COMMENT '工具ID',
  `tool_code` varchar(100) NOT NULL COMMENT '工具编码',
  `tool_name` varchar(100) NOT NULL COMMENT '工具名称',
  `book_quantity` int NOT NULL DEFAULT '0' COMMENT '账面数量',
  `actual_quantity` int NOT NULL DEFAULT '0' COMMENT '实际数量',
  `diff_quantity` int NOT NULL DEFAULT '0' COMMENT '差异数量',
  `status` varchar(20) NOT NULL DEFAULT '正常' COMMENT '状态: 正常/盘盈/盘亏',
  `remark` longtext COMMENT '备注',
  PRIMARY KEY (`id`),
  KEY `idx_tool_invent_created_1fc203` (`created_at`),
  KEY `idx_tool_invent_updated_b9b9a4` (`updated_at`),
  KEY `idx_tool_invent_invento_ece1d4` (`inventory_id`),
  KEY `idx_tool_invent_tool_id_365c31` (`tool_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tool_inventory_detail`
--

LOCK TABLES `tool_inventory_detail` WRITE;
/*!40000 ALTER TABLE `tool_inventory_detail` DISABLE KEYS */;
INSERT INTO `tool_inventory_detail` VALUES (1,'2026-07-10 15:37:00.204211','2026-07-10 15:37:00.204235',1,1,'111111111','1111111111',1,0,-1,'待盘点',NULL);
/*!40000 ALTER TABLE `tool_inventory_detail` ENABLE KEYS */;
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
