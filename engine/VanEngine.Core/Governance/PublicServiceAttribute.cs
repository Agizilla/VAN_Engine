using System.Reflection;

namespace VanEngine.Core.Governance;

[AttributeUsage(AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Class)]
public sealed class PublicServiceAttribute : Attribute
{
    public string ServiceDescription { get; }

    public PublicServiceAttribute(string description)
    {
        ServiceDescription = description;
    }
}

public static class PublicServiceValidator
{
    public static bool MayExposePublicInterface(MemberInfo member)
    {
        if (member.GetCustomAttribute<PublicServiceAttribute>() != null)
            return true;

        Console.WriteLine($"[UNIVERSAL LAW VIOLATION] Law 5: {member.Name} attempts public exposure without public service.");
        return false;
    }

    public static bool HasPublicServiceAttribute(Type type)
    {
        return type.GetCustomAttribute<PublicServiceAttribute>() != null;
    }

    public static bool HasPublicServiceAttribute(object obj)
    {
        return HasPublicServiceAttribute(obj.GetType());
    }
}
