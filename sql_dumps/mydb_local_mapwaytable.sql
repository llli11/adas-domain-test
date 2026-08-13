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
-- Table structure for table `mapwaytable`
--

DROP TABLE IF EXISTS `mapwaytable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mapwaytable` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `area` varchar(255) DEFAULT NULL COMMENT '泛化区域',
  `city` longtext NOT NULL COMMENT '城市列表（逗号分隔）',
  `project_type` varchar(32) NOT NULL DEFAULT 'cooperative' COMMENT '项目类型: cooperative(合作项目) / self_developed(自研)',
  PRIMARY KEY (`id`),
  KEY `idx_mapwaytable_created_e64cc9` (`created_at`),
  KEY `idx_mapwaytable_updated_da58be` (`updated_at`),
  KEY `idx_mapwaytable_project_08f15f` (`project_type`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='区域数据表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mapwaytable`
--

LOCK TABLES `mapwaytable` WRITE;
/*!40000 ALTER TABLE `mapwaytable` DISABLE KEYS */;
INSERT INTO `mapwaytable` VALUES (17,'2026-05-27 09:15:07.743218','2026-06-22 19:52:56.891153','区域1','长春、长沙、成都、大连、福州、广州','cooperative'),(18,'2026-05-27 09:18:51.791177','2026-06-22 19:57:57.039126','区域2','贵阳、邯郸、杭州、合肥、济南','cooperative'),(19,'2026-05-27 09:19:07.347172','2026-06-22 19:57:57.040693','区域3','兰州、南昌、南京、南宁、厦门、苏州','cooperative'),(20,'2026-05-27 09:19:19.728433','2026-06-26 21:33:20.327629','区域4','深圳、沈阳、石家庄、重庆、太原','cooperative'),(21,'2026-05-27 09:21:27.664583','2026-06-26 23:09:29.617111','区域5','武汉、西安、郑州','cooperative'),(25,'2026-06-26 19:09:28.209146','2026-07-06 15:12:40.793781','1','武汉、长沙、北京','self_developed'),(26,'2026-06-26 13:39:56.011473','2026-07-06 15:12:40.786776','2','杭州、重庆、贵州、上海、深圳、厦门','self_developed');
/*!40000 ALTER TABLE `mapwaytable` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:31
