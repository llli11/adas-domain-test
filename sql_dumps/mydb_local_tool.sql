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
-- Table structure for table `tool`
--

DROP TABLE IF EXISTS `tool`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tool` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `tool_code` varchar(100) NOT NULL COMMENT '设备编号',
  `tool_name` varchar(100) NOT NULL COMMENT '设备名称',
  `tool_type` varchar(50) NOT NULL COMMENT '设备类别',
  `specification` varchar(200) DEFAULT NULL COMMENT '规格型号',
  `brand` varchar(50) DEFAULT NULL COMMENT '品牌',
  `quantity` int NOT NULL DEFAULT '1' COMMENT '设备数量',
  `unit` varchar(20) NOT NULL DEFAULT '个' COMMENT '单位',
  `location` varchar(100) DEFAULT NULL COMMENT '存放位置',
  `status` varchar(100) NOT NULL DEFAULT '可用' COMMENT '状态: 可用/借出/维修/报废',
  `purchase_date` date DEFAULT NULL COMMENT '购买日期',
  `warranty_period` varchar(50) DEFAULT NULL COMMENT '保修期限',
  `responsible_person` varchar(50) DEFAULT NULL COMMENT '负责人',
  `image_url` varchar(500) DEFAULT NULL COMMENT '设备图片URL',
  `current_user` varchar(50) DEFAULT NULL COMMENT '当前使用者',
  `is_in_stock` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否在库',
  `remark` longtext COMMENT '备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `tool_code` (`tool_code`),
  KEY `idx_tool_created_f6123b` (`created_at`),
  KEY `idx_tool_updated_4df7fb` (`updated_at`),
  KEY `idx_tool_tool_co_8fbd38` (`tool_code`),
  KEY `idx_tool_tool_na_d8752a` (`tool_name`),
  KEY `idx_tool_tool_ty_9a09bc` (`tool_type`),
  KEY `idx_tool_status_ef0dca` (`status`),
  KEY `idx_tool_is_in_s_55d59c` (`is_in_stock`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tool`
--

LOCK TABLES `tool` WRITE;
/*!40000 ALTER TABLE `tool` DISABLE KEYS */;
INSERT INTO `tool` VALUES (1,'2026-06-29 20:16:46.176953','2026-07-10 15:36:49.519494','111111111','1111111111','111111111',NULL,NULL,1,'个',NULL,'可用',NULL,NULL,NULL,'/api/v1/tool/image/20260710073648.jpg','111111111111',1,'');
/*!40000 ALTER TABLE `tool` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:29
