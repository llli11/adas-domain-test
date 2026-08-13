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
-- Table structure for table `tool_inventory`
--

DROP TABLE IF EXISTS `tool_inventory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tool_inventory` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `task_code` varchar(50) NOT NULL COMMENT '盘点任务编码',
  `task_name` varchar(100) NOT NULL COMMENT '盘点任务名称',
  `inventory_date` date NOT NULL COMMENT '盘点日期',
  `status` varchar(20) NOT NULL DEFAULT '待盘点' COMMENT '状态: 待盘点/进行中/已完成',
  `responsible_person` varchar(50) DEFAULT NULL COMMENT '责任人姓名',
  `total_count` int NOT NULL DEFAULT '0' COMMENT '应盘数量',
  `actual_count` int NOT NULL DEFAULT '0' COMMENT '实盘数量',
  `diff_count` int NOT NULL DEFAULT '0' COMMENT '差异数量',
  `diff_explanation` longtext COMMENT '差异说明',
  `complete_time` datetime(6) DEFAULT NULL COMMENT '完成时间',
  `remark` longtext COMMENT '备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_code` (`task_code`),
  KEY `idx_tool_invent_created_374794` (`created_at`),
  KEY `idx_tool_invent_updated_31d733` (`updated_at`),
  KEY `idx_tool_invent_task_co_a501b2` (`task_code`),
  KEY `idx_tool_invent_task_na_0dc8e9` (`task_name`),
  KEY `idx_tool_invent_invento_5899c3` (`inventory_date`),
  KEY `idx_tool_invent_status_f78e02` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tool_inventory`
--

LOCK TABLES `tool_inventory` WRITE;
/*!40000 ALTER TABLE `tool_inventory` DISABLE KEYS */;
INSERT INTO `tool_inventory` VALUES (1,'2026-07-10 15:37:00.193341','2026-08-13 08:46:07.478542','INV1783669015289','1111','2026-07-10','已完成','11',1,0,1,'','2026-08-13 00:46:07.476422','');
/*!40000 ALTER TABLE `tool_inventory` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:34
