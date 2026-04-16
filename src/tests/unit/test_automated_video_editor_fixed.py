    print(f"📊 OVERALL RESULT: {summary['overall_result']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    print(f"✅ Capabilities Demonstrated: {len(results['capabilities_demonstrated'])}")

    print("\n🏆 DEMONSTRATED CAPABILITIES:")
    for capability in results["capabilities_demonstrated"]:
        print(f"   • {capability}")

    if results["quality_metrics"]:
        quality = results["quality_metrics"]
        print("\n📈 QUALITY METRICS:")
        print(f"   • Overall score: {quality['overall_score']:.1f}/10")
        print(f"   • Grade: {quality.get('quality_grade', 'N/A')}")

    print("\n💡 RECOMMENDATIONS:")
    for rec in results["recommendations"]:
        print(f"   {rec}")

    return results