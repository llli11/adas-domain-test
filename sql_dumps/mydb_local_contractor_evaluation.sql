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
-- Table structure for table `contractor_evaluation`
--

DROP TABLE IF EXISTS `contractor_evaluation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contractor_evaluation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `staff_id` int NOT NULL COMMENT '人员ID',
  `evaluation_month` varchar(7) NOT NULL COMMENT '考核周期 YYYY-MM',
  `attitude_score` decimal(4,1) DEFAULT NULL COMMENT '工作态度评分（0-10）',
  `ability_score` decimal(4,1) DEFAULT NULL COMMENT '工作能力评分（0-10）',
  `achievement_score` decimal(4,1) DEFAULT NULL COMMENT '工作达成评分（0-10）',
  `quality_score` decimal(5,2) DEFAULT NULL COMMENT '任务质量评分（自动计算）',
  `mistake_total` int NOT NULL DEFAULT '0' COMMENT '当月犯错总次数',
  `mistake_deduction` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '犯错减分（自动计算，每次-0.1）',
  `final_score` decimal(5,2) DEFAULT NULL COMMENT '月度绩效分数（自动计算）',
  `assessor` varchar(50) DEFAULT NULL COMMENT '考核人',
  `assessment_date` datetime(6) DEFAULT NULL COMMENT '考核日期',
  `reward_bonus` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '奖励加分（自动计算，每次+0.1）',
  `reward_total` int NOT NULL DEFAULT '0' COMMENT '当月奖励总次数',
  PRIMARY KEY (`id`),
  KEY `idx_contractor__created_5211f9` (`created_at`),
  KEY `idx_contractor__updated_40a47f` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='外委月度考评记录';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contractor_evaluation`
--

LOCK TABLES `contractor_evaluation` WRITE;
/*!40000 ALTER TABLE `contractor_evaluation` DISABLE KEYS */;
/*!40000 ALTER TABLE `contractor_evaluation` ENABLE KEYS */;
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
